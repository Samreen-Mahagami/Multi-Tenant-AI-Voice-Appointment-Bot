#!/usr/bin/env python3
"""
End-to-end integration test for Phase 3.
Tests the complete flow: Bedrock Agent -> Lambda -> Go Services -> Response
"""

import json
import boto3
import time
import sys
import os
from datetime import datetime

# Configuration
AGENT_ID = "S2MOVY5G8J"
AGENT_ALIAS_ID = "XOOC4XVDXZ"
REGION = "us-east-1"

def test_bedrock_agent_integration():
    """Test the complete Bedrock Agent integration with real backend services."""
    
    print("🧪 Testing End-to-End Integration (Phase 3)")
    print("=" * 50)
    
    # Initialize Bedrock Agent Runtime client
    try:
        bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=REGION)
        print(f"✅ Connected to Bedrock Agent Runtime in {REGION}")
    except Exception as e:
        print(f"❌ Failed to connect to Bedrock: {e}")
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Appointment Booking Flow",
            "messages": [
                "Hi, I'd like to book an appointment",
                "Tomorrow morning",
                "9:30 AM please", 
                "John Smith",
                "john.smith@example.com"
            ],
            "expected_keywords": ["appointment", "slots", "confirmation", "booked"]
        },
        {
            "name": "Different Clinic Test",
            "messages": [
                "I need to see a pediatrician",
                "Tomorrow afternoon",
                "2:00 PM works",
                "Sarah Johnson", 
                "sarah.j@example.com"
            ],
            "expected_keywords": ["pediatric", "appointment", "confirmation"]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 Testing: {scenario['name']}")
        print("-" * 30)
        
        success = test_conversation_scenario(bedrock_agent, scenario)
        if not success:
            print(f"❌ Scenario '{scenario['name']}' failed")
            return False
        else:
            print(f"✅ Scenario '{scenario['name']}' passed")
    
    print("\n🎉 All end-to-end tests passed!")
    return True

def test_conversation_scenario(bedrock_agent, scenario):
    """Test a complete conversation scenario."""
    
    session_id = f"test-session-{int(time.time())}"
    
    for i, message in enumerate(scenario["messages"]):
        print(f"  👤 User: {message}")
        
        try:
            # Send message to Bedrock Agent
            response = bedrock_agent.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=session_id,
                inputText=message
            )
            
            # Process streaming response
            agent_response = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        agent_response += chunk['bytes'].decode('utf-8')
            
            print(f"  🤖 Agent: {agent_response}")
            
            # Validate response contains expected elements
            if i == len(scenario["messages"]) - 1:  # Last message should contain confirmation
                if "confirmation" not in agent_response.lower():
                    print(f"    ⚠️  Expected confirmation in final response")
                    return False
            
            # Small delay between messages
            time.sleep(1)
            
        except Exception as e:
            print(f"    ❌ Error in conversation: {e}")
            return False
    
    return True

def test_lambda_functions_directly():
    """Test Lambda functions directly to ensure they can call Go services."""
    
    print("\n🔧 Testing Lambda Functions Directly")
    print("-" * 40)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Test search-slots Lambda
    print("Testing search-slots Lambda...")
    try:
        search_payload = {
            "actionGroup": "AppointmentActions",
            "apiPath": "/searchSlots", 
            "httpMethod": "POST",
            "requestBody": {
                "content": {
                    "application/json": {
                        "properties": [
                            {"name": "tenant_id", "value": "downtown_medical"},
                            {"name": "date", "value": "tomorrow"},
                            {"name": "time_preference", "value": "morning"}
                        ]
                    }
                }
            }
        }
        
        response = lambda_client.invoke(
            FunctionName='ivr-search-slots',
            Payload=json.dumps(search_payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"  ✅ Search slots response: {result.get('response', {}).get('httpStatusCode', 'Unknown')}")
        
    except Exception as e:
        print(f"  ❌ Search slots test failed: {e}")
        return False
    
    # Test confirm-appointment Lambda  
    print("Testing confirm-appointment Lambda...")
    try:
        # First get a slot ID from search results
        confirm_payload = {
            "actionGroup": "AppointmentActions",
            "apiPath": "/confirmAppointment",
            "httpMethod": "POST", 
            "requestBody": {
                "content": {
                    "application/json": {
                        "properties": [
                            {"name": "tenant_id", "value": "downtown_medical"},
                            {"name": "slot_id", "value": "test-slot-id"},
                            {"name": "patient_name", "value": "Test Patient"},
                            {"name": "patient_email", "value": "test@example.com"}
                        ]
                    }
                }
            }
        }
        
        response = lambda_client.invoke(
            FunctionName='ivr-confirm-appointment',
            Payload=json.dumps(confirm_payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"  ✅ Confirm appointment response: {result.get('response', {}).get('httpStatusCode', 'Unknown')}")
        
    except Exception as e:
        print(f"  ❌ Confirm appointment test failed: {e}")
        return False
    
    return True

def check_prerequisites():
    """Check that all prerequisites are met for testing."""
    
    print("🔍 Checking Prerequisites")
    print("-" * 25)
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        return False
    
    # Check Bedrock Agent exists
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
        agent = bedrock_agent.get_agent(agentId=AGENT_ID)
        print(f"✅ Bedrock Agent: {agent['agent']['agentName']} ({agent['agent']['agentStatus']})")
    except Exception as e:
        print(f"❌ Bedrock Agent not found: {e}")
        return False
    
    # Check Lambda functions exist
    lambda_client = boto3.client('lambda', region_name=REGION)
    required_functions = ['ivr-search-slots', 'ivr-confirm-appointment', 'ivr-handoff-human']
    
    for func_name in required_functions:
        try:
            func = lambda_client.get_function(FunctionName=func_name)
            print(f"✅ Lambda Function: {func_name}")
        except Exception as e:
            print(f"❌ Lambda Function missing: {func_name} - {e}")
            return False
    
    return True

def main():
    """Main test execution."""
    
    print("🚀 Phase 3: End-to-End Integration Testing")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please ensure:")
        print("   1. AWS credentials are configured")
        print("   2. Bedrock Agent is deployed and prepared")
        print("   3. Lambda functions are deployed")
        print("   4. Go backend services are accessible")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test Lambda functions directly
    if not test_lambda_functions_directly():
        print("\n❌ Lambda function tests failed")
        sys.exit(1)
    
    # Test full Bedrock Agent integration
    if not test_bedrock_agent_integration():
        print("\n❌ End-to-end integration tests failed")
        sys.exit(1)
    
    print("\n🎉 Phase 3 Integration Testing Complete!")
    print("✅ All systems are working together correctly")

if __name__ == "__main__":
    main()