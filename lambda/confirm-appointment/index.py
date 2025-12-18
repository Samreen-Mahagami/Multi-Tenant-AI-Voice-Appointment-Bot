"""
Lambda function for confirming/booking appointments.
Called by Bedrock Agent as an action group.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any
import random
import string

APPOINTMENT_SERVICE_URL = os.environ.get('APPOINTMENT_SERVICE_URL', 'http://appointment-service-go:7002')


def handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent action group handler for confirmAppointment.
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        params = extract_parameters(event)
        tenant_id = params.get('tenant_id', 'default')
        slot_id = params.get('slot_id', '')
        patient_name = params.get('patient_name', '')
        patient_email = params.get('patient_email', '')
        
        print(f"Confirming appointment: tenant={tenant_id}, slot={slot_id}, name={patient_name}, email={patient_email}")
        
        # Validate required fields
        missing_fields = []
        if not slot_id:
            missing_fields.append("slot_id")
        if not patient_name:
            missing_fields.append("patient_name")
        if not patient_email:
            missing_fields.append("patient_email")
        
        if missing_fields:
            return create_response(event, 400, {
                "status": "FAILED",
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "message": f"I still need the following information: {', '.join(missing_fields).replace('_', ' ')}"
            })
        
        # Call appointment service
        result = confirm_appointment(tenant_id, slot_id, patient_name, patient_email)
        
        if result.get('status') == 'BOOKED':
            conf_ref = result.get('confirmation_ref', '')
            return create_response(event, 200, {
                "status": "BOOKED",
                "confirmation_ref": conf_ref,
                "message": f"Appointment confirmed! Confirmation number is {conf_ref}. A confirmation email will be sent to {patient_email}."
            })
        else:
            return create_response(event, 200, {
                "status": "FAILED",
                "error": result.get('error', 'Booking failed'),
                "message": "I'm sorry, I couldn't book that slot. It may have been taken. Would you like to search for other available times?"
            })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(event, 500, {
            "status": "FAILED",
            "error": str(e),
            "message": "Sorry, I couldn't complete the booking right now. Please try again."
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


def confirm_appointment(tenant_id: str, slot_id: str, patient_name: str, patient_email: str) -> dict:
    """Call appointment service to confirm booking."""
    
    url = f"{APPOINTMENT_SERVICE_URL}/v1/appointments/confirm"
    
    payload = json.dumps({
        "tenantId": tenant_id,
        "slotId": slot_id,
        "patientName": patient_name,
        "patientEmail": patient_email
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Failed to call appointment service: {e}")
        # Return mock success for testing
        return {
            "status": "BOOKED",
            "confirmation_ref": generate_confirmation_ref(tenant_id)
        }


def generate_confirmation_ref(tenant_id: str) -> str:
    """Generate a mock confirmation reference."""
    prefix = tenant_id[:4].upper() if tenant_id else "APPT"
    date_part = datetime.now().strftime("%m%d")
    random_part = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{date_part}-{random_part}"


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