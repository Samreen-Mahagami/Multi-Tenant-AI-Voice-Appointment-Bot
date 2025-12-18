#!/usr/bin/env python3
"""
Voice Client for Multi-Tenant AI Voice Appointment Bot
Real-time voice interaction using microphone and speakers
"""

import pyaudio
import wave
import json
import base64
import requests
import threading
import time
import io
from datetime import datetime
import argparse

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available. Audio playback may not work.")

class VoiceClient:
    def __init__(self, api_endpoint, tenant_did='1001'):
        self.api_endpoint = api_endpoint
        self.tenant_did = tenant_did
        self.session_id = f"client-{int(time.time())}"
        
        # Audio configuration
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5  # Max recording length
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Initialize pygame for audio playback
        if PYGAME_AVAILABLE:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Clinic information
        self.clinics = {
            '1001': 'Downtown Medical Center',
            '1002': 'Westside Family Practice', 
            '1003': 'Pediatric Care Clinic'
        }
        
        print(f"🎙️  Voice Client initialized")
        print(f"   Clinic: {self.clinics.get(tenant_did, 'Unknown')} (DID: {tenant_did})")
        print(f"   Session: {self.session_id}")
        print(f"   API: {api_endpoint}")
    
    def record_audio(self):
        """Record audio from microphone"""
        print("🎤 Recording... (speak now, press Enter when done)")
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        recording = True
        
        def stop_recording():
            nonlocal recording
            input()  # Wait for Enter key
            recording = False
        
        # Start thread to listen for Enter key
        stop_thread = threading.Thread(target=stop_recording)
        stop_thread.daemon = True
        stop_thread.start()
        
        start_time = time.time()
        while recording and (time.time() - start_time) < self.record_seconds:
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        
        wav_data = wav_buffer.getvalue()
        print(f"✅ Recorded {len(wav_data)} bytes of audio")
        
        return wav_data
    
    def play_audio(self, audio_data, audio_format='mp3'):
        """Play audio response"""
        if not PYGAME_AVAILABLE:
            print("🔊 Audio playback not available (pygame not installed)")
            return
        
        try:
            # Save audio to temporary file
            temp_file = f"/tmp/response_{int(time.time())}.{audio_format}"
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Play audio
            print("🔊 Playing response...")
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            import os
            os.remove(temp_file)
            
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
    
    def send_voice_request(self, audio_data):
        """Send voice data to API and get response"""
        try:
            # Encode audio as base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request
            payload = {
                'sessionId': self.session_id,
                'tenantDid': self.tenant_did,
                'audioData': audio_b64
            }
            
            print("🚀 Sending voice request to API...")
            
            # Send request
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Response received:")
                print(f"   Text: {result.get('responseText', 'No text')}")
                
                # Play audio response
                if 'responseAudio' in result:
                    response_audio = base64.b64decode(result['responseAudio'])
                    self.play_audio(response_audio, result.get('audioFormat', 'mp3'))
                
                return result
            else:
                print(f"❌ API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def start_conversation(self):
        """Start interactive voice conversation"""
        print("\n🎯 Starting Voice Conversation")
        print("=" * 50)
        print("Instructions:")
        print("- Press Enter to start recording")
        print("- Speak your message")
        print("- Press Enter again to stop recording")
        print("- Type 'quit' to exit")
        print("=" * 50)
        
        conversation_count = 0
        
        while True:
            conversation_count += 1
            print(f"\n--- Turn {conversation_count} ---")
            
            # Check if user wants to quit
            user_input = input("Press Enter to record (or 'quit' to exit): ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            # Record audio
            try:
                audio_data = self.record_audio()
                
                # Send to API
                response = self.send_voice_request(audio_data)
                
                if response:
                    response_text = response.get('responseText', '')
                    
                    # Check if conversation should end
                    if any(phrase in response_text.lower() for phrase in 
                           ['goodbye', 'thank you for calling', 'have a great day']):
                        print("📞 Conversation ended by agent")
                        break
                else:
                    print("❌ Failed to get response. Try again.")
                
            except KeyboardInterrupt:
                print("\n👋 Conversation interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error during conversation: {e}")
        
        print("\n📞 Voice conversation ended")
        print(f"   Total turns: {conversation_count}")
        print(f"   Session: {self.session_id}")
    
    def test_connection(self):
        """Test connection to voice API"""
        print("🔍 Testing API connection...")
        
        # Create a simple test audio (silence)
        test_audio = b'\x00' * 1024  # 1KB of silence
        
        try:
            response = self.send_voice_request(test_audio)
            if response:
                print("✅ API connection successful")
                return True
            else:
                print("❌ API connection failed")
                return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        self.audio.terminate()
        if PYGAME_AVAILABLE:
            pygame.mixer.quit()

def main():
    parser = argparse.ArgumentParser(description='Voice Client for Multi-Tenant AI Voice Bot')
    parser.add_argument('--api', required=True, help='Voice API endpoint URL')
    parser.add_argument('--did', default='1001', choices=['1001', '1002', '1003'], 
                       help='Clinic DID (default: 1001)')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    
    args = parser.parse_args()
    
    # Initialize client
    client = VoiceClient(args.api, args.did)
    
    try:
        if args.test:
            # Test mode
            success = client.test_connection()
            exit(0 if success else 1)
        else:
            # Interactive mode
            client.start_conversation()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        client.cleanup()

if __name__ == "__main__":
    # Check dependencies
    try:
        import pyaudio
    except ImportError:
        print("❌ PyAudio not installed. Install with: pip install pyaudio")
        exit(1)
    
    main()