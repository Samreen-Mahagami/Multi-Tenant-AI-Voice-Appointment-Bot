import json
import boto3
import base64
import urllib.parse
from xml.sax.saxutils import escape

def lambda_handler(event, context):
    """Handle Twilio webhook and bridge to voice processor"""
    
    # Parse Twilio webhook data
    if event.get('body'):
        # Parse form data from Twilio
        body = urllib.parse.parse_qs(event['body'])
        
        # Extract call information
        call_sid = body.get('CallSid', [''])[0]
        from_number = body.get('From', [''])[0]
        to_number = body.get('To', [''])[0]
        speech_result = body.get('SpeechResult', ['Hello'])[0]
        
        # Determine DID from called number (last 4 digits)
        did = '1001'  # Default
        if '1002' in to_number:
            did = '1002'
        elif '1003' in to_number:
            did = '1003'
        
        print(f"Twilio call: {call_sid}, DID: {did}, Speech: {speech_result}")
        
        # Call voice processor Lambda
        lambda_client = boto3.client('lambda')
        
        voice_payload = {
            'text': speech_result,
            'did': did,
            'session_id': f'twilio-{call_sid}'
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName='IvrVoiceStack-VoiceProcessorFunction11F26011-trz1dxgnXLEW',
                Payload=json.dumps(voice_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result['statusCode'] == 200:
                body_data = json.loads(result['body'])
                agent_response = body_data['agent_response']
            else:
                agent_response = "I'm sorry, I'm having technical difficulties."
                
        except Exception as e:
            print(f"Error calling voice processor: {e}")
            agent_response = "I'm sorry, there was an error processing your request."
        
        # Create TwiML response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{escape(agent_response)}</Say>
    <Gather input="speech" action="/voice" method="POST" speechTimeout="5">
        <Say voice="alice">Please continue speaking, or hang up when finished.</Say>
    </Gather>
    <Say voice="alice">Thank you for calling. Goodbye!</Say>
</Response>"""
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/xml'
            },
            'body': twiml
        }
    
    # Initial call - just start the conversation
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! Welcome to our AI voice appointment bot. Please tell me how I can help you.</Say>
    <Gather input="speech" action="/voice" method="POST" speechTimeout="5">
        <Say voice="alice">Please speak after the beep.</Say>
    </Gather>
    <Say voice="alice">I didn't hear anything. Please try calling again.</Say>
</Response>"""
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/xml'
        },
        'body': twiml
    }