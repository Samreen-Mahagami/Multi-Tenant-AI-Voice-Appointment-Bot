import json
import boto3
import base64
import uuid
import time
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
polly = boto3.client('polly', region_name='us-east-1')
transcribe = boto3.client('transcribe', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

# Configuration
BEDROCK_AGENT_ID = 'S2MOVY5G8J'
BEDROCK_AGENT_ALIAS_ID = 'XOOC4XVDXZ'
S3_BUCKET = 'clinic-voice-processing'  # You'll need to create this

# Clinic configurations with voice settings
CLINIC_VOICES = {
    '1001': {
        'name': 'Downtown Medical Center',
        'voice_id': 'Joanna',
        'engine': 'neural',
        'greeting': 'Hello, thank you for calling Downtown Medical Center. How can I help you today?'
    },
    '1002': {
        'name': 'Westside Family Practice',
        'voice_id': 'Matthew', 
        'engine': 'neural',
        'greeting': 'Hi there! You\'ve reached Westside Family Practice. How may I assist you today?'
    },
    '1003': {
        'name': 'Pediatric Care Clinic',
        'voice_id': 'Salli',
        'engine': 'neural',
        'greeting': 'Welcome to Pediatric Care Clinic! We\'re here to help with your child\'s health needs.'
    }
}

def lambda_handler(event, context):
    """
    Main Lambda handler for voice processing
    Handles both Amazon Connect and direct voice API calls
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Determine the source of the call
        if 'Details' in event and 'ContactData' in event['Details']:
            # Amazon Connect call
            return handle_connect_call(event, context)
        elif 'audio_data' in event:
            # Direct API call with audio
            return handle_direct_voice_call(event, context)
        else:
            # Text-based call (for testing)
            return handle_text_call(event, context)
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def handle_connect_call(event, context):
    """Handle Amazon Connect voice calls"""
    try:
        # Extract Connect event data
        contact_data = event.get('Details', {}).get('ContactData', {})
        contact_id = contact_data.get('ContactId', '')
        
        # Extract DID from dialed number
        system_endpoint = contact_data.get('SystemEndpoint', {})
        dialed_number = system_endpoint.get('Address', '')
        did = extract_did_from_number(dialed_number)
        
        # Get parameters from Connect
        parameters = event.get('Details', {}).get('Parameters', {})
        user_input = parameters.get('userInput', '')
        audio_url = parameters.get('audioUrl', '')
        
        logger.info(f"Connect call - DID: {did}, Contact: {contact_id}")
        
        # Process the voice input
        if audio_url:
            # Transcribe audio from Connect
            transcribed_text = transcribe_audio_from_url(audio_url)
        else:
            # Use text input (for DTMF or text-based testing)
            transcribed_text = user_input or "Hello"
        
        # Get clinic configuration
        clinic_config = CLINIC_VOICES.get(did, CLINIC_VOICES['1001'])
        
        # Generate session ID
        session_id = f"connect-{did}-{contact_id}"
        
        # Call Bedrock Agent
        agent_response = call_bedrock_agent(session_id, transcribed_text, did)
        
        # Generate speech audio
        audio_url = generate_speech(agent_response, clinic_config['voice_id'], clinic_config['engine'])
        
        return {
            'statusCode': 200,
            'agentResponse': agent_response,
            'audioUrl': audio_url,
            'sessionId': session_id,
            'did': did,
            'clinicName': clinic_config['name']
        }
        
    except Exception as e:
        logger.error(f"Error in handle_connect_call: {str(e)}")
        return {
            'statusCode': 500,
            'agentResponse': "I'm sorry, I'm having technical difficulties. Please hold while I transfer you to a representative.",
            'error': str(e)
        }

def handle_direct_voice_call(event, context):
    """Handle direct API calls with audio data"""
    try:
        # Extract audio data and metadata
        audio_data = event.get('audio_data', '')
        did = event.get('did', '1001')
        session_id = event.get('session_id', f"direct-{did}-{int(time.time())}")
        audio_format = event.get('audio_format', 'wav')
        
        logger.info(f"Direct voice call - DID: {did}, Session: {session_id}")
        
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Transcribe the audio
        transcribed_text = transcribe_audio_bytes(audio_bytes, audio_format)
        
        # Get clinic configuration
        clinic_config = CLINIC_VOICES.get(did, CLINIC_VOICES['1001'])
        
        # Call Bedrock Agent
        agent_response = call_bedrock_agent(session_id, transcribed_text, did)
        
        # Generate speech audio
        audio_url = generate_speech(agent_response, clinic_config['voice_id'], clinic_config['engine'])
        
        # Also return base64 encoded audio for direct use
        audio_base64 = generate_speech_base64(agent_response, clinic_config['voice_id'], clinic_config['engine'])
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'transcribed_text': transcribed_text,
                'agent_response': agent_response,
                'audio_url': audio_url,
                'audio_base64': audio_base64,
                'session_id': session_id,
                'did': did,
                'clinic_name': clinic_config['name'],
                'voice_id': clinic_config['voice_id']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in handle_direct_voice_call: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Voice processing failed',
                'message': str(e)
            })
        }

def handle_text_call(event, context):
    """Handle text-based calls (for testing)"""
    try:
        # Extract text input
        user_input = event.get('text', event.get('inputText', 'Hello'))
        did = event.get('did', '1001')
        session_id = event.get('session_id', f"text-{did}-{int(time.time())}")
        
        logger.info(f"Text call - DID: {did}, Input: {user_input}")
        
        # Get clinic configuration
        clinic_config = CLINIC_VOICES.get(did, CLINIC_VOICES['1001'])
        
        # Call Bedrock Agent
        agent_response = call_bedrock_agent(session_id, user_input, did)
        
        # Generate speech audio
        audio_url = generate_speech(agent_response, clinic_config['voice_id'], clinic_config['engine'])
        audio_base64 = generate_speech_base64(agent_response, clinic_config['voice_id'], clinic_config['engine'])
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'user_input': user_input,
                'agent_response': agent_response,
                'audio_url': audio_url,
                'audio_base64': audio_base64,
                'session_id': session_id,
                'did': did,
                'clinic_name': clinic_config['name'],
                'voice_id': clinic_config['voice_id']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in handle_text_call: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Text processing failed',
                'message': str(e)
            })
        }

def extract_did_from_number(phone_number):
    """Extract DID from phone number"""
    if not phone_number:
        return '1001'
    
    # Look for DID patterns in the number
    if '1001' in phone_number:
        return '1001'
    elif '1002' in phone_number:
        return '1002'
    elif '1003' in phone_number:
        return '1003'
    else:
        # Default to Downtown Medical
        return '1001'

def transcribe_audio_from_url(audio_url):
    """Transcribe audio from a URL using Amazon Transcribe"""
    try:
        job_name = f"transcribe-{uuid.uuid4().hex[:8]}-{int(time.time())}"
        
        # Start transcription job
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_url},
            MediaFormat='wav',  # Adjust based on your audio format
            LanguageCode='en-US',
            Settings={
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1
            }
        )
        
        # Wait for completion (with timeout)
        max_wait_time = 30  # seconds
        wait_time = 0
        
        while wait_time < max_wait_time:
            job_status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            status = job_status['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get the transcript
                transcript_uri = job_status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                # Download and parse transcript (implementation depends on your setup)
                return "I need an appointment"  # Placeholder - implement actual transcript parsing
            elif status == 'FAILED':
                logger.error(f"Transcription failed: {job_status}")
                return "Hello"
            
            time.sleep(2)
            wait_time += 2
        
        logger.warning("Transcription timeout")
        return "Hello"
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return "Hello"

def transcribe_audio_bytes(audio_bytes, audio_format):
    """Transcribe audio from bytes using Amazon Transcribe"""
    try:
        # For real-time transcription, you might want to use Amazon Transcribe Streaming
        # For now, we'll upload to S3 and use regular Transcribe
        
        # Upload audio to S3
        audio_key = f"audio/{uuid.uuid4().hex}.{audio_format}"
        s3.put_object(Bucket=S3_BUCKET, Key=audio_key, Body=audio_bytes)
        
        # Transcribe from S3
        audio_url = f"s3://{S3_BUCKET}/{audio_key}"
        return transcribe_audio_from_url(audio_url)
        
    except Exception as e:
        logger.error(f"Audio transcription error: {str(e)}")
        return "Hello"

def call_bedrock_agent(session_id, input_text, did):
    """Call AWS Bedrock Agent"""
    try:
        logger.info(f"Calling Bedrock Agent - Session: {session_id}, DID: {did}, Input: {input_text}")
        
        response = bedrock_agent.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=f"[DID: {did}] {input_text}"
        )
        
        # Parse streaming response
        agent_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        logger.info(f"Bedrock Agent response: {agent_response}")
        return agent_response.strip() or "I'm here to help you with your appointment needs."
        
    except Exception as e:
        logger.error(f"Bedrock Agent error: {str(e)}")
        return "I'm sorry, I'm having trouble processing your request right now. Let me transfer you to a human representative."

def generate_speech(text, voice_id, engine='neural'):
    """Generate speech using Amazon Polly and return S3 URL"""
    try:
        logger.info(f"Generating speech with voice {voice_id}: {text[:50]}...")
        
        # Generate speech with Polly
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine=engine,
            SampleRate='22050'
        )
        
        # Upload to S3
        audio_key = f"speech/{uuid.uuid4().hex}.mp3"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=audio_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )
        
        # Generate presigned URL
        audio_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': audio_key},
            ExpiresIn=3600  # 1 hour
        )
        
        return audio_url
        
    except Exception as e:
        logger.error(f"Speech generation error: {str(e)}")
        return None

def generate_speech_base64(text, voice_id, engine='neural'):
    """Generate speech using Amazon Polly and return base64 encoded audio"""
    try:
        # Generate speech with Polly
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine=engine,
            SampleRate='22050'
        )
        
        # Read audio stream and encode as base64
        audio_bytes = response['AudioStream'].read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return audio_base64
        
    except Exception as e:
        logger.error(f"Speech generation error: {str(e)}")
        return None