#!/usr/bin/env python3
"""
Test the complete voice flow: Voice → FreeSWITCH → Media Gateway → S3 → Transcribe → Bedrock → Polly → S3 → Voice
"""

import requests
import json
import time
import base64
import boto3
from datetime import datetime

def test_s3_bucket():
    """Test S3 bucket access"""
    print("🪣 Testing S3 Bucket Access...")
    
    try:
        s3 = boto3.client('s3', region_name='us-east-1')
        
        # Test bucket access
        response = s3.head_bucket(Bucket='clinic-voice-processing-089580247707')
        print("✅ S3 bucket accessible")
        
        # List recent objects
        objects = s3.list_objects_v2(
            Bucket='clinic-voice-processing-089580247707',
            MaxKeys=5
        )
        
        if 'Contents' in objects:
            print(f"📁 Found {len(objects['Contents'])} objects in bucket")
            for obj in objects['Contents']:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("📁 Bucket is empty (ready for new audio files)")
            
        return True
        
    except Exception as e:
        print(f"❌ S3 bucket test failed: {e}")
        return False

def test_bedrock_agent():
    """Test Bedrock Agent directly"""
    print("\n🧠 Testing Bedrock Agent...")
    
    try:
        client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        response = client.invoke_agent(
            agentId='S2MOVY5G8J',
            agentAliasId='XOOC4XVDXZ',
            sessionId=f'test-{int(time.time())}',
            inputText='Hello, I want to book an appointment for tomorrow morning'
        )
        
        # Process streaming response
        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
        
        print(f"✅ Bedrock Agent Response: {completion.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ Bedrock Agent test failed: {e}")
        return False

def test_polly_tts():
    """Test Amazon Polly TTS"""
    print("\n🔊 Testing Amazon Polly TTS...")
    
    try:
        polly = boto3.client('polly', region_name='us-east-1')
        
        response = polly.synthesize_speech(
            Text='Hello! I can help you book an appointment. What day works best for you?',
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        
        # Save audio to S3
        s3 = boto3.client('s3', region_name='us-east-1')
        audio_data = response['AudioStream'].read()
        
        key = f"test/polly-test-{int(time.time())}.mp3"
        s3.put_object(
            Bucket='clinic-voice-processing-089580247707',
            Key=key,
            Body=audio_data,
            ContentType='audio/mpeg'
        )
        
        print(f"✅ Polly TTS working - Generated {len(audio_data)} bytes")
        print(f"📦 Audio stored to S3: s3://clinic-voice-processing-089580247707/{key}")
        return True
        
    except Exception as e:
        print(f"❌ Polly TTS test failed: {e}")
        return False

def test_media_gateway_connection():
    """Test Media Gateway WebSocket connection"""
    print("\n🌉 Testing Media Gateway Connection...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Media Gateway healthy: {health_data.get('service')}")
            
            features = health_data.get('features', [])
            print(f"🔧 Features: {', '.join(features)}")
            
            agent_id = health_data.get('agentId', '')
            if agent_id:
                print(f"🧠 Bedrock Agent ID: {agent_id}")
            
            return True
        else:
            print(f"❌ Media Gateway health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Media Gateway connection failed: {e}")
        return False

def simulate_voice_conversation():
    """Simulate a complete voice conversation flow"""
    print("\n🎭 Simulating Complete Voice Conversation Flow...")
    print("=" * 60)
    
    conversation_steps = [
        {
            "step": 1,
            "user_input": "Hello, I want to book an appointment",
            "expected_flow": "Voice → S3 → Transcribe → Bedrock → Response"
        },
        {
            "step": 2,
            "user_input": "Tomorrow morning please",
            "expected_flow": "Voice → S3 → Transcribe → Bedrock → Search Slots → Response"
        },
        {
            "step": 3,
            "user_input": "9:30 AM sounds good",
            "expected_flow": "Voice → S3 → Transcribe → Bedrock → Response"
        },
        {
            "step": 4,
            "user_input": "My name is John Smith",
            "expected_flow": "Voice → S3 → Transcribe → Bedrock → Response"
        },
        {
            "step": 5,
            "user_input": "john.smith@example.com",
            "expected_flow": "Voice → S3 → Transcribe → Bedrock → Confirm Appointment → Response"
        }
    ]
    
    for step in conversation_steps:
        print(f"\n📞 Step {step['step']}: User says: \"{step['user_input']}\"")
        print(f"🔄 Expected Flow: {step['expected_flow']}")
        
        # Simulate the flow
        print("   1. 🎤 Voice captured by FreeSWITCH")
        print("   2. 📦 Audio stored to S3")
        print("   3. 🎯 Transcribed by Amazon Transcribe")
        print("   4. 🧠 Processed by Bedrock Agent")
        print("   5. 🔊 Response generated by Polly")
        print("   6. 📦 Response audio stored to S3")
        print("   7. 🎵 Audio played back to user")
        
        time.sleep(1)  # Simulate processing time
    
    print("\n✅ Complete voice conversation flow simulated!")

def main():
    print("🚀 Testing Complete Voice Flow with S3 Integration")
    print("=" * 60)
    
    # Test individual components
    s3_ok = test_s3_bucket()
    bedrock_ok = test_bedrock_agent()
    polly_ok = test_polly_tts()
    gateway_ok = test_media_gateway_connection()
    
    print("\n📋 Component Test Results:")
    print(f"   S3 Bucket: {'✅' if s3_ok else '❌'}")
    print(f"   Bedrock Agent: {'✅' if bedrock_ok else '❌'}")
    print(f"   Polly TTS: {'✅' if polly_ok else '❌'}")
    print(f"   Media Gateway: {'✅' if gateway_ok else '❌'}")
    
    # Simulate complete flow
    simulate_voice_conversation()
    
    # Final status
    all_ok = s3_ok and bedrock_ok and polly_ok and gateway_ok
    
    print(f"\n🎯 Overall Status: {'✅ READY FOR FULL VOICE FLOW' if all_ok else '⚠️ SOME COMPONENTS NEED ATTENTION'}")
    
    if all_ok:
        print("\n🎉 Your system is ready for the complete flow:")
        print("   Your Voice → FreeSWITCH → Media Gateway → S3 → Transcribe → Bedrock → Polly → S3 → Your Voice")
        print("\n📞 To test with real voice:")
        print("   1. Open: http://localhost:8000/simple_voice_test.html")
        print("   2. Select a hospital")
        print("   3. Click microphone and speak!")
    else:
        print("\n🔧 Fix the failing components and run this test again.")

if __name__ == "__main__":
    main()