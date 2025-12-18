#!/usr/bin/env python3
"""
Setup Live Voice Testing with Amazon Connect
Creates a real phone number you can call to test the voice bot
"""

import boto3
import json
import time
import uuid
from datetime import datetime

class LiveVoiceSetup:
    def __init__(self):
        self.connect = boto3.client('connect', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.s3 = boto3.client('s3', region_name='us-east-1')
        
        # Configuration
        self.instance_alias = 'clinic-voice-bot'
        self.voice_function_name = 'IvrVoiceStack-VoiceProcessorFunction11F26011-trz1dxgnXLEW'
        self.bucket_name = f'clinic-voice-processing-{boto3.Session().get_credentials().access_key[:8].lower()}'
        
    def create_s3_bucket(self):
        """Create S3 bucket for audio processing"""
        print("📦 Creating S3 bucket for audio processing...")
        
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 bucket already exists: {self.bucket_name}")
        except:
            # Create bucket
            try:
                self.s3.create_bucket(Bucket=self.bucket_name)
                print(f"✅ Created S3 bucket: {self.bucket_name}")
                
                # Set bucket policy for Lambda access
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "lambda.amazonaws.com"
                            },
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject"
                            ],
                            "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                        }
                    ]
                }
                
                self.s3.put_bucket_policy(
                    Bucket=self.bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                
            except Exception as e:
                print(f"❌ Failed to create S3 bucket: {e}")
                return False
        
        # Update Lambda environment variable
        try:
            self.lambda_client.update_function_configuration(
                FunctionName=self.voice_function_name,
                Environment={
                    'Variables': {
                        'BEDROCK_AGENT_ID': 'S2MOVY5G8J',
                        'BEDROCK_AGENT_ALIAS_ID': 'XOOC4XVDXZ',
                        'TENANT_CONFIG_URL': 'https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod',
                        'APPOINTMENT_SERVICE_URL': 'https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod',
                        'S3_BUCKET': self.bucket_name
                    }
                }
            )
            print("✅ Updated Lambda environment variables")
        except Exception as e:
            print(f"⚠️  Warning: Could not update Lambda environment: {e}")
        
        return True
    
    def create_connect_instance(self):
        """Create Amazon Connect instance"""
        print("🏗️  Creating Amazon Connect instance...")
        
        try:
            # Check if instance already exists
            instances = self.connect.list_instances()
            for instance in instances['InstanceSummaryList']:
                if instance['InstanceAlias'] == self.instance_alias:
                    print(f"✅ Connect instance already exists: {instance['Id']}")
                    return instance['Id'], instance['Arn']
            
            # Create new instance
            response = self.connect.create_instance(
                InstanceAlias=self.instance_alias,
                IdentityManagementType='CONNECT_MANAGED',
                InboundCallsEnabled=True,
                OutboundCallsEnabled=False
            )
            
            instance_id = response['Id']
            instance_arn = response['Arn']
            
            print(f"✅ Created Connect instance: {instance_id}")
            
            # Wait for instance to be active
            print("⏳ Waiting for instance to become active...")
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    instance_info = self.connect.describe_instance(InstanceId=instance_id)
                    if instance_info['Instance']['InstanceStatus'] == 'ACTIVE':
                        print("✅ Instance is now active")
                        break
                except:
                    pass
                
                time.sleep(10)
                wait_time += 10
                print(f"   Still waiting... ({wait_time}s)")
            
            return instance_id, instance_arn
            
        except Exception as e:
            print(f"❌ Failed to create Connect instance: {e}")
            return None, None
    
    def claim_phone_number(self, instance_id):
        """Claim a phone number for testing"""
        print("📞 Claiming phone number...")
        
        try:
            # Search for available toll-free numbers
            available_numbers = self.connect.search_available_phone_numbers(
                TargetArn=f"arn:aws:connect:us-east-1:{boto3.Session().get_credentials().access_key}:instance/{instance_id}",
                PhoneNumberCountryCode='US',
                PhoneNumberType='TOLL_FREE'
            )
            
            if not available_numbers['AvailableNumbersList']:
                print("❌ No toll-free numbers available, trying DID...")
                # Try DID numbers
                available_numbers = self.connect.search_available_phone_numbers(
                    TargetArn=f"arn:aws:connect:us-east-1:{boto3.Session().get_credentials().access_key}:instance/{instance_id}",
                    PhoneNumberCountryCode='US',
                    PhoneNumberType='DID'
                )
            
            if available_numbers['AvailableNumbersList']:
                phone_number = available_numbers['AvailableNumbersList'][0]['PhoneNumber']
                
                # Claim the number
                response = self.connect.claim_phone_number(
                    TargetArn=f"arn:aws:connect:us-east-1:{boto3.Session().get_credentials().access_key}:instance/{instance_id}",
                    PhoneNumber=phone_number
                )
                
                phone_number_id = response['PhoneNumberId']
                print(f"✅ Claimed phone number: {phone_number}")
                return phone_number, phone_number_id
            else:
                print("❌ No phone numbers available")
                return None, None
                
        except Exception as e:
            print(f"❌ Failed to claim phone number: {e}")
            return None, None
    
    def create_contact_flow(self, instance_id):
        """Create contact flow for voice bot"""
        print("📋 Creating contact flow...")
        
        # Simple contact flow that calls our Lambda function
        contact_flow_content = {
            "Version": "2019-10-30",
            "StartAction": "12345678-1234-1234-1234-123456789012",
            "Actions": [
                {
                    "Identifier": "12345678-1234-1234-1234-123456789012",
                    "Type": "MessageParticipant",
                    "Parameters": {
                        "Text": "Hello! Welcome to our AI voice appointment bot. Please speak after the beep."
                    },
                    "Transitions": {
                        "NextAction": "87654321-4321-4321-4321-210987654321"
                    }
                },
                {
                    "Identifier": "87654321-4321-4321-4321-210987654321",
                    "Type": "GetParticipantInput",
                    "Parameters": {
                        "InputType": "Speech",
                        "TimeoutSeconds": 10,
                        "MaxDigits": 1
                    },
                    "Transitions": {
                        "NextAction": "11111111-2222-3333-4444-555555555555",
                        "Errors": [
                            {
                                "NextAction": "99999999-8888-7777-6666-555555555555",
                                "ErrorType": "InputTimeLimitExceeded"
                            }
                        ]
                    }
                },
                {
                    "Identifier": "11111111-2222-3333-4444-555555555555",
                    "Type": "InvokeExternalResource",
                    "Parameters": {
                        "FunctionArn": f"arn:aws:lambda:us-east-1:{boto3.Session().get_credentials().access_key}:function:{self.voice_function_name}",
                        "TimeoutSeconds": 30
                    },
                    "Transitions": {
                        "NextAction": "22222222-3333-4444-5555-666666666666",
                        "Errors": [
                            {
                                "NextAction": "99999999-8888-7777-6666-555555555555",
                                "ErrorType": "NoMatchingError"
                            }
                        ]
                    }
                },
                {
                    "Identifier": "22222222-3333-4444-5555-666666666666",
                    "Type": "MessageParticipant",
                    "Parameters": {
                        "Text": "$.External.agentResponse"
                    },
                    "Transitions": {
                        "NextAction": "87654321-4321-4321-4321-210987654321"
                    }
                },
                {
                    "Identifier": "99999999-8888-7777-6666-555555555555",
                    "Type": "MessageParticipant",
                    "Parameters": {
                        "Text": "I'm sorry, I didn't catch that. Please try again or hold for a representative."
                    },
                    "Transitions": {
                        "NextAction": "33333333-4444-5555-6666-777777777777"
                    }
                },
                {
                    "Identifier": "33333333-4444-5555-6666-777777777777",
                    "Type": "DisconnectParticipant",
                    "Parameters": {}
                }
            ]
        }
        
        try:
            response = self.connect.create_contact_flow(
                InstanceId=instance_id,
                Name="AI Voice Appointment Bot",
                Type='CONTACT_FLOW',
                Description="Multi-tenant AI voice appointment booking system",
                Content=json.dumps(contact_flow_content)
            )
            
            contact_flow_id = response['ContactFlowId']
            contact_flow_arn = response['ContactFlowArn']
            
            print(f"✅ Created contact flow: {contact_flow_id}")
            return contact_flow_id, contact_flow_arn
            
        except Exception as e:
            print(f"❌ Failed to create contact flow: {e}")
            return None, None
    
    def associate_phone_with_flow(self, instance_id, phone_number_id, contact_flow_id):
        """Associate phone number with contact flow"""
        print("🔗 Associating phone number with contact flow...")
        
        try:
            self.connect.associate_phone_number_contact_flow(
                PhoneNumberId=phone_number_id,
                InstanceId=instance_id,
                ContactFlowId=contact_flow_id
            )
            print("✅ Phone number associated with contact flow")
            return True
        except Exception as e:
            print(f"❌ Failed to associate phone number: {e}")
            return False
    
    def test_voice_function(self):
        """Test the voice processing Lambda function"""
        print("🧪 Testing voice processing function...")
        
        test_payload = {
            'text': 'Hello, I need an appointment',
            'did': '1001',
            'session_id': f'test-{int(time.time())}'
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.voice_function_name,
                Payload=json.dumps(test_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                print(f"✅ Voice function test successful")
                print(f"   Response: {body['agent_response'][:100]}...")
                return True
            else:
                print(f"❌ Voice function test failed: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Voice function test error: {e}")
            return False
    
    def setup_complete_system(self):
        """Set up the complete live voice testing system"""
        print("🚀 Setting Up Live Voice Testing System")
        print("=" * 60)
        print(f"⏰ Setup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Create S3 bucket
        if not self.create_s3_bucket():
            return False
        
        # Step 2: Test voice function
        if not self.test_voice_function():
            print("❌ Voice function not working. Please check deployment.")
            return False
        
        # Step 3: Create Connect instance
        instance_id, instance_arn = self.create_connect_instance()
        if not instance_id:
            return False
        
        # Step 4: Claim phone number
        phone_number, phone_number_id = self.claim_phone_number(instance_id)
        if not phone_number:
            print("⚠️  Could not claim phone number automatically.")
            print("   You can claim one manually in the Connect console.")
            return False
        
        # Step 5: Create contact flow
        contact_flow_id, contact_flow_arn = self.create_contact_flow(instance_id)
        if not contact_flow_id:
            return False
        
        # Step 6: Associate phone with flow
        if not self.associate_phone_with_flow(instance_id, phone_number_id, contact_flow_id):
            return False
        
        # Success!
        print("\n" + "=" * 60)
        print("🎉 LIVE VOICE TESTING READY!")
        print("=" * 60)
        
        print(f"📞 **CALL THIS NUMBER TO TEST**: {phone_number}")
        print(f"🏥 Instance ID: {instance_id}")
        print(f"📋 Contact Flow ID: {contact_flow_id}")
        print(f"🔧 Lambda Function: {self.voice_function_name}")
        print(f"📦 S3 Bucket: {self.bucket_name}")
        
        print("\n🎯 **HOW TO TEST**:")
        print(f"1. Call: {phone_number}")
        print("2. Wait for greeting")
        print("3. Say: 'I need an appointment'")
        print("4. Continue conversation with the AI bot")
        print("5. Bot will respond with voice!")
        
        print("\n📊 **MONITORING**:")
        print(f"   Connect Console: https://console.aws.amazon.com/connect/")
        print(f"   Lambda Logs: https://console.aws.amazon.com/cloudwatch/")
        print(f"   S3 Bucket: https://console.aws.amazon.com/s3/")
        
        print("\n💰 **ESTIMATED COST**: ~$0.05 per test call")
        
        return True

def main():
    print("📞 Live Voice Testing Setup for Multi-Tenant AI Voice Bot")
    print("=" * 60)
    print("This will create a real phone number you can call to test voice interactions.")
    print("The bot will use speech-to-text and text-to-speech for real conversations.")
    print()
    
    confirm = input("Proceed with live voice setup? This will create AWS resources. (y/N): ")
    if confirm.lower() != 'y':
        print("Setup cancelled.")
        return
    
    setup = LiveVoiceSetup()
    
    try:
        success = setup.setup_complete_system()
        
        if success:
            print("\n✅ Setup completed successfully!")
            print("🎉 You now have a live voice bot you can call and test!")
        else:
            print("\n❌ Setup failed. Check the error messages above.")
    
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")

if __name__ == "__main__":
    main()