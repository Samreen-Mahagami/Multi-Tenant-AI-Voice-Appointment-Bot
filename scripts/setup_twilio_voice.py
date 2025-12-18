#!/usr/bin/env python3
"""
Setup Live Voice Testing with Twilio
Creates a real phone number you can call to test the voice bot
Works with any AWS account (including AISPL accounts)
"""

import boto3
import json
import requests
import base64
from datetime import datetime

class TwilioVoiceSetup:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.apigateway = boto3.client('apigateway', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        
        # Configuration
        self.voice_function_name = 'IvrVoiceStack-VoiceProcessorFunction11F26011-trz1dxgnXLEW'
        self.webhook_function_name = 'twilio-voice-webhook'
        
    def create_twilio_webhook_lambda(self):
        """Create Lambda function to handle Twilio webhooks"""
        print("🔗 Creating Twilio webhook Lambda function...")
        
        webhook_code = '''
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
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{}</Say>
    <Gather input="speech" action="/voice" method="POST" speechTimeout="5">
        <Say voice="alice">Please continue speaking, or hang up when finished.</Say>
    </Gather>
    <Say voice="alice">Thank you for calling. Goodbye!</Say>
</Response>""".format(escape(agent_response))
        
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
'''
        
        try:
            # Create IAM role for webhook Lambda
            role_arn = self.create_webhook_lambda_role()
            
            # Create the Lambda function
            response = self.lambda_client.create_function(
                FunctionName=self.webhook_function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='index.lambda_handler',
                Code={'ZipFile': webhook_code.encode()},
                Description='Twilio webhook handler for voice bot',
                Timeout=30,
                Environment={
                    'Variables': {
                        'VOICE_FUNCTION_NAME': self.voice_function_name
                    }
                }
            )
            
            function_arn = response['FunctionArn']
            print(f"✅ Created webhook Lambda: {function_arn}")
            return function_arn
            
        except Exception as e:
            if 'already exists' in str(e):
                print("✅ Webhook Lambda already exists")
                # Get existing function ARN
                response = self.lambda_client.get_function(FunctionName=self.webhook_function_name)
                return response['Configuration']['FunctionArn']
            else:
                print(f"❌ Failed to create webhook Lambda: {e}")
                return None
    
    def create_webhook_lambda_role(self):
        """Create IAM role for webhook Lambda"""
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Create role
            response = self.iam.create_role(
                RoleName='twilio-webhook-lambda-role',
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for Twilio webhook Lambda function'
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName='twilio-webhook-lambda-role',
                    PolicyArn=policy
                )
            
            # Add policy to invoke other Lambda functions
            lambda_invoke_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "lambda:InvokeFunction",
                        "Resource": "*"
                    }
                ]
            }
            
            self.iam.put_role_policy(
                RoleName='twilio-webhook-lambda-role',
                PolicyName='LambdaInvokePolicy',
                PolicyDocument=json.dumps(lambda_invoke_policy)
            )
            
            # Wait for role to propagate
            import time
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            if 'already exists' in str(e):
                # Get existing role
                response = self.iam.get_role(RoleName='twilio-webhook-lambda-role')
                return response['Role']['Arn']
            else:
                raise e
    
    def create_api_gateway(self, lambda_arn):
        """Create API Gateway for Twilio webhooks"""
        print("🌐 Creating API Gateway for webhooks...")
        
        try:
            # Create REST API
            api_response = self.apigateway.create_rest_api(
                name='twilio-voice-webhook-api',
                description='API for Twilio voice webhooks'
            )
            
            api_id = api_response['id']
            print(f"✅ Created API Gateway: {api_id}")
            
            # Get root resource
            resources = self.apigateway.get_resources(restApiId=api_id)
            root_resource_id = None
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_resource_id = resource['id']
                    break
            
            # Create /voice resource
            voice_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=root_resource_id,
                pathPart='voice'
            )
            
            voice_resource_id = voice_resource['id']
            
            # Create POST method
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=voice_resource_id,
                httpMethod='POST',
                authorizationType='NONE'
            )
            
            # Set up Lambda integration
            account_id = boto3.Session().get_credentials().access_key
            lambda_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=voice_resource_id,
                httpMethod='POST',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=lambda_uri
            )
            
            # Deploy API
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName='prod'
            )
            
            # Add Lambda permission for API Gateway
            self.lambda_client.add_permission(
                FunctionName=self.webhook_function_name,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:us-east-1:{account_id}:{api_id}/*/*"
            )
            
            webhook_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/voice"
            print(f"✅ Webhook URL: {webhook_url}")
            
            return webhook_url
            
        except Exception as e:
            print(f"❌ Failed to create API Gateway: {e}")
            return None
    
    def setup_twilio_instructions(self, webhook_url):
        """Provide instructions for Twilio setup"""
        print("\n" + "=" * 60)
        print("🎉 TWILIO VOICE BOT SETUP COMPLETE!")
        print("=" * 60)
        
        print(f"🔗 **Webhook URL**: {webhook_url}")
        
        print("\n📞 **NEXT STEPS TO GET A PHONE NUMBER**:")
        print("1. Go to https://www.twilio.com/try-twilio")
        print("2. Sign up for free account (gets $15 credit)")
        print("3. Verify your phone number")
        print("4. Go to Phone Numbers → Manage → Buy a number")
        print("5. Choose a number and purchase it (~$1/month)")
        
        print("\n⚙️  **CONFIGURE YOUR TWILIO NUMBER**:")
        print("6. In Twilio Console, go to Phone Numbers → Manage → Active numbers")
        print("7. Click on your purchased number")
        print("8. In 'Voice & Fax' section:")
        print(f"   - Webhook: {webhook_url}")
        print("   - HTTP Method: POST")
        print("9. Save configuration")
        
        print("\n🧪 **TEST YOUR VOICE BOT**:")
        print("10. Call your Twilio phone number")
        print("11. Say: 'I need an appointment'")
        print("12. Bot will respond with voice!")
        print("13. Continue the conversation")
        
        print("\n💰 **COSTS**:")
        print("   - Phone number: ~$1/month")
        print("   - Incoming calls: ~$0.0085/minute")
        print("   - Text-to-speech: ~$0.016 per 1M characters")
        print("   - Total per call: ~$0.02")
        
        print("\n🔧 **TROUBLESHOOTING**:")
        print(f"   - Check Lambda logs: {self.webhook_function_name}")
        print(f"   - Check voice processor logs: {self.voice_function_name}")
        print("   - Verify webhook URL in Twilio console")
        
        return True
    
    def setup_complete_system(self):
        """Set up the complete Twilio voice system"""
        print("🚀 Setting Up Twilio Voice Testing System")
        print("=" * 60)
        print(f"⏰ Setup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("This works with any AWS account (including AISPL accounts)")
        print("=" * 60)
        
        # Step 1: Create webhook Lambda
        lambda_arn = self.create_twilio_webhook_lambda()
        if not lambda_arn:
            return False
        
        # Step 2: Create API Gateway
        webhook_url = self.create_api_gateway(lambda_arn)
        if not webhook_url:
            return False
        
        # Step 3: Provide setup instructions
        return self.setup_twilio_instructions(webhook_url)

def main():
    print("📞 Twilio Live Voice Testing Setup")
    print("=" * 50)
    print("This creates a webhook for Twilio voice calls.")
    print("You'll get a real phone number to call and test voice interactions.")
    print("Works with any AWS account!")
    print()
    
    confirm = input("Proceed with Twilio voice setup? (y/N): ")
    if confirm.lower() != 'y':
        print("Setup cancelled.")
        return
    
    setup = TwilioVoiceSetup()
    
    try:
        success = setup.setup_complete_system()
        
        if success:
            print("\n✅ Setup completed successfully!")
            print("🎉 Follow the instructions above to get your phone number!")
        else:
            print("\n❌ Setup failed. Check the error messages above.")
    
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")

if __name__ == "__main__":
    main()