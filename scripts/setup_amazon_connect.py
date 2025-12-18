#!/usr/bin/env python3
"""
Amazon Connect Setup for Multi-Tenant AI Voice Appointment Bot
Automates the setup of Amazon Connect for live phone testing
"""

import boto3
import json
import time
from datetime import datetime

class AmazonConnectSetup:
    def __init__(self):
        self.connect = boto3.client('connect')
        self.lambda_client = boto3.client('lambda')
        self.iam = boto3.client('iam')
        
        # Configuration
        self.instance_alias = 'clinic-voice-bot'
        self.bedrock_agent_id = 'S2MOVY5G8J'
        self.bedrock_agent_alias_id = 'XOOC4XVDXZ'
        
        # Clinic configuration
        self.clinics = {
            '1001': {
                'name': 'Downtown Medical Center',
                'greeting': 'Hello, thank you for calling Downtown Medical Center. How can I help you today?'
            },
            '1002': {
                'name': 'Westside Family Practice', 
                'greeting': 'Hi there! You\'ve reached Westside Family Practice. How may I assist you today?'
            },
            '1003': {
                'name': 'Pediatric Care Clinic',
                'greeting': 'Welcome to Pediatric Care Clinic! We\'re here to help with your child\'s health needs.'
            }
        }
    
    def create_connect_instance(self):
        """Create Amazon Connect instance"""
        print("🏗️  Creating Amazon Connect instance...")
        
        try:
            response = self.connect.create_instance(
                InstanceAlias=self.instance_alias,
                IdentityManagementType='CONNECT_MANAGED',
                InboundCallsEnabled=True,
                OutboundCallsEnabled=False
            )
            
            instance_id = response['Id']
            instance_arn = response['Arn']
            
            print(f"✅ Connect instance created: {instance_id}")
            print(f"   ARN: {instance_arn}")
            
            # Wait for instance to be active
            print("⏳ Waiting for instance to become active...")
            waiter = self.connect.get_waiter('instance_created')
            waiter.wait(InstanceId=instance_id)
            
            return instance_id, instance_arn
            
        except Exception as e:
            print(f"❌ Failed to create Connect instance: {e}")
            return None, None
    
    def create_bedrock_lambda(self):
        """Create Lambda function to bridge Connect and Bedrock Agent"""
        print("🔗 Creating Bedrock Agent Lambda bridge...")
        
        lambda_code = '''
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Bridge Amazon Connect to Bedrock Agent"""
    
    # Extract Connect event data
    contact_id = event.get('Details', {}).get('ContactData', {}).get('ContactId', '')
    customer_endpoint = event.get('Details', {}).get('ContactData', {}).get('CustomerEndpoint', {})
    system_endpoint = event.get('Details', {}).get('ContactData', {}).get('SystemEndpoint', {})
    
    # Extract DID from dialed number
    dialed_number = system_endpoint.get('Address', '')
    did = dialed_number[-4:] if len(dialed_number) >= 4 else '1001'  # Default to 1001
    
    # Get user input from Connect
    user_input = event.get('Details', {}).get('Parameters', {}).get('userInput', 'Hello')
    
    logger.info(f"Processing call for DID: {did}, Input: {user_input}")
    
    try:
        # Call Bedrock Agent
        bedrock = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        session_id = f"connect-{did}-{contact_id}"
        
        response = bedrock.invoke_agent(
            agentId='S2MOVY5G8J',
            agentAliasId='XOOC4XVDXZ', 
            sessionId=session_id,
            inputText=f"[DID: {did}] {user_input}"
        )
        
        # Parse Bedrock response
        agent_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        logger.info(f"Bedrock response: {agent_response}")
        
        return {
            'statusCode': 200,
            'agentResponse': agent_response or "I'm here to help you with your appointment needs.",
            'sessionId': session_id,
            'did': did
        }
        
    except Exception as e:
        logger.error(f"Error calling Bedrock Agent: {e}")
        return {
            'statusCode': 500,
            'agentResponse': "I'm sorry, I'm having technical difficulties. Let me transfer you to a human representative.",
            'error': str(e)
        }
'''
        
        # Create Lambda function
        try:
            # Create execution role first
            role_arn = self.create_lambda_role()
            
            response = self.lambda_client.create_function(
                FunctionName='clinic-bedrock-agent-bridge',
                Runtime='python3.9',
                Role=role_arn,
                Handler='index.lambda_handler',
                Code={'ZipFile': lambda_code.encode()},
                Description='Bridge Amazon Connect to Bedrock Agent for clinic appointments',
                Timeout=30,
                Environment={
                    'Variables': {
                        'BEDROCK_AGENT_ID': self.bedrock_agent_id,
                        'BEDROCK_AGENT_ALIAS_ID': self.bedrock_agent_alias_id
                    }
                }
            )
            
            function_arn = response['FunctionArn']
            print(f"✅ Lambda function created: {function_arn}")
            return function_arn
            
        except Exception as e:
            print(f"❌ Failed to create Lambda function: {e}")
            return None
    
    def create_lambda_role(self):
        """Create IAM role for Lambda function"""
        
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
                RoleName='clinic-bedrock-lambda-role',
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for clinic Bedrock Agent Lambda bridge'
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName='clinic-bedrock-lambda-role',
                    PolicyArn=policy
                )
            
            # Wait for role to propagate
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            print(f"Warning: Role creation failed (may already exist): {e}")
            # Try to get existing role
            try:
                response = self.iam.get_role(RoleName='clinic-bedrock-lambda-role')
                return response['Role']['Arn']
            except:
                raise e
    
    def create_contact_flow(self, instance_id, lambda_arn):
        """Create contact flow for each clinic"""
        print("📞 Creating contact flows...")
        
        contact_flows = {}
        
        for did, clinic in self.clinics.items():
            flow_content = {
                "Version": "2019-10-30",
                "StartAction": "greeting",
                "Actions": [
                    {
                        "Identifier": "greeting",
                        "Type": "MessageParticipant",
                        "Parameters": {
                            "Text": clinic['greeting']
                        },
                        "Transitions": {
                            "NextAction": "get_input"
                        }
                    },
                    {
                        "Identifier": "get_input",
                        "Type": "GetParticipantInput",
                        "Parameters": {
                            "InputType": "Speech",
                            "TimeoutSeconds": 10,
                            "MaxDigits": 1
                        },
                        "Transitions": {
                            "NextAction": "invoke_bedrock",
                            "Errors": [
                                {
                                    "NextAction": "invoke_bedrock",
                                    "ErrorType": "InputTimeLimitExceeded"
                                }
                            ]
                        }
                    },
                    {
                        "Identifier": "invoke_bedrock",
                        "Type": "InvokeExternalResource",
                        "Parameters": {
                            "FunctionArn": lambda_arn,
                            "TimeoutSeconds": 8
                        },
                        "Transitions": {
                            "NextAction": "speak_response"
                        }
                    },
                    {
                        "Identifier": "speak_response",
                        "Type": "MessageParticipant",
                        "Parameters": {
                            "Text": "$.External.agentResponse"
                        },
                        "Transitions": {
                            "NextAction": "get_input"
                        }
                    }
                ]
            }
            
            try:
                response = self.connect.create_contact_flow(
                    InstanceId=instance_id,
                    Name=f"{clinic['name']} Voice Bot",
                    Type='CONTACT_FLOW',
                    Description=f"Voice appointment bot for {clinic['name']} (DID: {did})",
                    Content=json.dumps(flow_content)
                )
                
                contact_flows[did] = response['ContactFlowArn']
                print(f"✅ Contact flow created for {clinic['name']}: {response['ContactFlowId']}")
                
            except Exception as e:
                print(f"❌ Failed to create contact flow for {clinic['name']}: {e}")
        
        return contact_flows
    
    def claim_phone_numbers(self, instance_id, contact_flows):
        """Claim phone numbers for each clinic"""
        print("📱 Claiming phone numbers...")
        
        phone_numbers = {}
        
        for did, clinic in self.clinics.items():
            try:
                # Search for available numbers
                available_numbers = self.connect.search_available_phone_numbers(
                    TargetArn=f"arn:aws:connect:us-east-1:{boto3.Session().get_credentials().access_key}:instance/{instance_id}",
                    PhoneNumberCountryCode='US',
                    PhoneNumberType='TOLL_FREE'
                )
                
                if available_numbers['AvailableNumbersList']:
                    phone_number = available_numbers['AvailableNumbersList'][0]['PhoneNumber']
                    
                    # Claim the number
                    response = self.connect.claim_phone_number(
                        TargetArn=f"arn:aws:connect:us-east-1:{boto3.Session().get_credentials().access_key}:instance/{instance_id}",
                        PhoneNumber=phone_number
                    )
                    
                    # Associate with contact flow
                    if did in contact_flows:
                        self.connect.associate_phone_number_contact_flow(
                            PhoneNumberId=response['PhoneNumberId'],
                            InstanceId=instance_id,
                            ContactFlowId=contact_flows[did].split('/')[-1]
                        )
                    
                    phone_numbers[did] = {
                        'number': phone_number,
                        'clinic': clinic['name'],
                        'id': response['PhoneNumberId']
                    }
                    
                    print(f"✅ Phone number claimed for {clinic['name']}: {phone_number}")
                
            except Exception as e:
                print(f"❌ Failed to claim number for {clinic['name']}: {e}")
        
        return phone_numbers
    
    def setup_complete_system(self):
        """Set up the complete Amazon Connect system"""
        print("🚀 Setting up Amazon Connect for Multi-Tenant Voice Bot")
        print("=" * 60)
        
        # Step 1: Create Connect instance
        instance_id, instance_arn = self.create_connect_instance()
        if not instance_id:
            return False
        
        # Step 2: Create Lambda bridge
        lambda_arn = self.create_bedrock_lambda()
        if not lambda_arn:
            return False
        
        # Step 3: Create contact flows
        contact_flows = self.create_contact_flow(instance_id, lambda_arn)
        
        # Step 4: Claim phone numbers
        phone_numbers = self.claim_phone_numbers(instance_id, contact_flows)
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 Amazon Connect Setup Complete!")
        print("=" * 60)
        
        print(f"📋 Connect Instance: {instance_id}")
        print(f"🔗 Lambda Function: clinic-bedrock-agent-bridge")
        
        print("\n📞 Phone Numbers:")
        for did, info in phone_numbers.items():
            print(f"   DID {did}: {info['number']} → {info['clinic']}")
        
        print("\n🧪 Testing Instructions:")
        print("1. Call each phone number")
        print("2. Say 'I need an appointment'")
        print("3. Follow the conversation flow")
        print("4. Verify appointment booking works")
        
        print("\n📊 Monitoring:")
        print(f"   Connect Console: https://console.aws.amazon.com/connect/")
        print(f"   Lambda Logs: https://console.aws.amazon.com/cloudwatch/")
        
        return True

def main():
    setup = AmazonConnectSetup()
    
    print("This script will set up Amazon Connect for live phone testing.")
    print("Estimated cost: ~$0.02 per test call")
    print("Setup time: ~10 minutes")
    
    confirm = input("\nProceed with setup? (y/N): ")
    if confirm.lower() != 'y':
        print("Setup cancelled.")
        return
    
    success = setup.setup_complete_system()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("You can now test with live phone calls.")
    else:
        print("\n❌ Setup failed. Check the error messages above.")

if __name__ == "__main__":
    main()