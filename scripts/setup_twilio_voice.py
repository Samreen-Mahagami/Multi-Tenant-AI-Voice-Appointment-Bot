#!/usr/bin/env python3
"""
Setup Live Voice Testing with Twilio
Creates API Gateway for Twilio webhooks using existing Lambda function
Works with any AWS account (including AISPL accounts)
"""

import boto3
import json
import requests
from datetime import datetime

class TwilioVoiceSetup:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.apigateway = boto3.client('apigateway', region_name='us-east-1')
        
        # Find the Twilio webhook function (deployed via CDK)
        self.webhook_function_name = None
        self.find_webhook_function()
    
    def find_webhook_function(self):
        """Find the Twilio webhook function deployed via CDK"""
        try:
            # List functions to find the Twilio webhook function
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    if 'TwilioWebhook' in function['FunctionName']:
                        self.webhook_function_name = function['FunctionName']
                        print(f"✅ Found Twilio webhook function: {self.webhook_function_name}")
                        return
            
            print("❌ Twilio webhook function not found. Please deploy the voice stack first:")
            print("   cd infrastructure && cdk deploy IvrVoiceStack")
            
        except Exception as e:
            print(f"❌ Error finding webhook function: {e}")
    
    def get_webhook_function_arn(self):
        """Get the ARN of the webhook function"""
        if not self.webhook_function_name:
            return None
            
        try:
            response = self.lambda_client.get_function(FunctionName=self.webhook_function_name)
            return response['Configuration']['FunctionArn']
        except Exception as e:
            print(f"❌ Error getting function ARN: {e}")
            return None
    
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
            
            # Get proper account ID
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            
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
        
        # Step 1: Get webhook Lambda ARN
        if not self.webhook_function_name:
            print("❌ Please deploy the voice stack first:")
            print("   cd infrastructure && cdk deploy IvrVoiceStack")
            return False
            
        lambda_arn = self.get_webhook_function_arn()
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