"""
Lambda function for searching available appointment slots.
Called by Bedrock Agent as an action group.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Any

APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL', 'http://localhost:7002')


def handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent action group handler for searchSlots.
    
    Event structure from Bedrock:
    {
        "actionGroup": "AppointmentActions",
        "apiPath": "/searchSlots",
        "httpMethod": "POST",
        "requestBody": {
            "content": {
                "application/json": {
                    "properties": [
                        {"name": "tenant_id", "value": "clinic_a"},
                        {"name": "date", "value": "tomorrow"},
                        {"name": "time_preference", "value": "morning"}
                    ]
                }
            }
        },
        "sessionAttributes": {...},
        "promptSessionAttributes": {...}
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract parameters from Bedrock Agent event
        params = extract_parameters(event)
        tenant_id = params.get('tenant_id', 'default')
        date = params.get('date', 'tomorrow')
        time_preference = params.get('time_preference', 'any')
        
        print(f"Searching slots: tenant={tenant_id}, date={date}, time_pref={time_preference}")
        
        # Call appointment service
        slots = search_slots(tenant_id, date, time_preference)
        
        # Format response for Bedrock Agent
        if slots:
            slots_text = format_slots_for_agent(slots)
            response_body = {
                "slots": slots,
                "message": f"Found {len(slots)} available slots: {slots_text}"
            }
        else:
            response_body = {
                "slots": [],
                "message": "No available slots found for the requested time. Please try a different date or time."
            }
        
        return create_response(event, 200, response_body)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(event, 500, {
            "error": str(e),
            "message": "Sorry, I couldn't search for appointments right now. Please try again."
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


def search_slots(tenant_id: str, date: str, time_preference: str) -> list:
    """Call appointment service to search for slots."""
    
    url = f"{APPOINTMENT_SERVICE_URL}/v1/slots/search"
    
    payload = json.dumps({
        "tenantId": tenant_id,
        "date": date,
        "timePreference": time_preference
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('slots', [])
    except urllib.error.URLError as e:
        print(f"Failed to call appointment service: {e}")
        # Return mock data for testing
        return generate_mock_slots(tenant_id, date, time_preference)


def generate_mock_slots(tenant_id: str, date: str, time_preference: str) -> list:
    """Generate mock slots for testing when service is unavailable."""
    base_time = datetime.now() + timedelta(days=1)
    
    if time_preference == 'morning':
        hours = [9, 9, 10]
        minutes = [0, 30, 0]
    elif time_preference == 'afternoon':
        hours = [14, 14, 15]
        minutes = [0, 30, 0]
    else:
        hours = [9, 14, 16]
        minutes = [30, 0, 30]
    
    slots = []
    for i, (h, m) in enumerate(zip(hours, minutes)):
        slot_time = base_time.replace(hour=h, minute=m, second=0, microsecond=0)
        slots.append({
            "slot_id": f"{tenant_id}-{slot_time.strftime('%Y%m%d')}-{h:02d}{m:02d}",
            "start_time": slot_time.isoformat(),
            "end_time": (slot_time + timedelta(minutes=30)).isoformat(),
            "doctor_name": f"Dr. {'Sharma' if i == 0 else 'Patel' if i == 1 else 'Kumar'}"
        })
    
    return slots


def format_slots_for_agent(slots: list) -> str:
    """Format slots as natural language for agent response."""
    formatted = []
    for i, slot in enumerate(slots[:3], 1):
        try:
            dt = datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M %p').lstrip('0')
            formatted.append(f"{time_str}")
        except:
            formatted.append(slot.get('start_time', 'Unknown'))
    
    return ", ".join(formatted)


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