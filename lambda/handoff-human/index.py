"""
Lambda function for initiating handoff to human receptionist.
Called by Bedrock Agent as an action group.
"""

import json
from typing import Any


def handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent action group handler for handoffToHuman.
    
    In a production system, this would:
    1. Notify the human receptionist queue
    2. Transfer the call via FreeSWITCH
    3. Log the handoff reason for analytics
    
    For this project, we simply signal the handoff.
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        params = extract_parameters(event)
        reason = params.get('reason', 'Caller requested human assistance')
        
        print(f"Handoff to human requested. Reason: {reason}")
        
        # In production: would trigger actual call transfer here
        # For now, we return a response that signals the Media Gateway
        # to handle the handoff
        
        response_body = {
            "status": "HANDOFF_INITIATED",
            "reason": reason,
            "message": "I'll connect you with a human receptionist right away. Please hold for just a moment.",
            "action": "TRANSFER_TO_HUMAN"
        }
        
        return create_response(event, 200, response_body)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(event, 500, {
            "status": "FAILED",
            "error": str(e),
            "message": "I'm having trouble connecting you. Please hold while I try again."
        })


def extract_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock Agent event structure."""
    params = {}
    
    try:
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        properties = json_content.get('properties', [])
        
        for prop in properties:
            name = prop.get('name')
            value = prop.get('value')
            if name and value:
                params[name] = value
                
    except Exception as e:
        print(f"Error extracting parameters: {e}")
    
    return params


def create_response(event: dict, status_code: int, body: dict) -> dict:
    """Create response in Bedrock Agent expected format."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            }
        }
    }