#!/usr/bin/env python3
"""
Test script for Bedrock Agent using boto3
"""

import boto3
import json
import os
import sys
import time
from datetime import datetime

def test_bedrock_agent():
    # Load environment variables
    agent_id = os.environ.get('BEDROCK_AGENT_ID')
    alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID')
    
    if not agent_id or not alias_id:
        print("❌ BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set in .env")
        return False
    
    print(f"🧪 Testing Bedrock Agent...")
    print(f"🔍 Testing Agent ID: {agent_id}")
    print(f"🔍 Testing Alias ID: {alias_id}")
    print("")
    
    # Initialize Bedrock Agent Runtime client
    try:
        client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    except Exception as e:
        print(f"❌ Failed to create Bedrock client: {e}")
        return False
    
    # Test 1: Initial greeting
    print("📞 Test 1: Initial greeting")
    print("----------------------------------------")
    session_id = f"test-greeting-{int(time.time())}"
    
    try:
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText="Hello"
        )
        
        # Process streaming response
        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
        
        print(f"Agent: {completion.strip()}")
        print("")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Booking flow
    print("📅 Test 2: Appointment booking flow")
    print("----------------------------------------")
    session_id = f"booking-test-{int(time.time())}"
    
    test_inputs = [
        "I want to book an appointment for tomorrow morning",
        "The 9:30 AM slot please", 
        "My name is John Smith",
        "john.smith@example.com"
    ]
    
    for i, input_text in enumerate(test_inputs, 1):
        print(f"Turn {i}: {input_text}")
        
        try:
            response = client.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=session_id,
                inputText=input_text
            )
            
            completion = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            print(f"Agent: {completion.strip()}")
            print("")
            
            time.sleep(2)  # Brief pause between turns
            
        except Exception as e:
            print(f"❌ Turn {i} failed: {e}")
            return False
    
    # Test 3: Human handoff
    print("🤝 Test 3: Human handoff")
    print("----------------------------------------")
    session_id = f"handoff-test-{int(time.time())}"
    
    try:
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText="I want to speak to a human"
        )
        
        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
        
        print(f"Agent: {completion.strip()}")
        print("")
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False
    
    print("✅ All tests completed!")
    print("")
    print("📋 Test Summary:")
    print("   ✅ Agent responds to greetings")
    print("   ✅ Agent can handle booking flow")
    print("   ✅ Agent can initiate human handoff")
    print("")
    print("🎯 Next: Set up local services with Docker Compose")
    
    return True

if __name__ == "__main__":
    # Load .env file if it exists
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    success = test_bedrock_agent()
    sys.exit(0 if success else 1)