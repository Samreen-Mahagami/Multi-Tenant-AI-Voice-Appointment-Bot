# Live Phone Call Testing Guide

## Overview
This guide shows you how to test your Multi-Tenant AI Voice Appointment Bot with real phone calls using different approaches.

## Testing Options (Easiest to Most Complex)

### 🥇 Option 1: Amazon Connect (Recommended - Easiest)

**Why Choose This:**
- No server setup required
- Native AWS integration with Bedrock
- Professional phone numbers
- Built-in speech recognition
- Pay-as-you-go pricing (~$0.018/minute)

**Setup Steps:**

#### 1. Create Amazon Connect Instance
```bash
# Via AWS Console
1. Go to Amazon Connect console
2. Click "Add an instance"
3. Choose "Store users within Amazon Connect"
4. Instance alias: "clinic-voice-bot"
5. Create administrator user
6. Enable telephony and data storage
```

#### 2. Claim Phone Numbers
```bash
# In Amazon Connect console
1. Go to "Phone numbers" 
2. Claim 3 phone numbers (one per clinic)
3. Note the numbers for each DID:
   - Downtown Medical: +1-555-XXX-1001
   - Westside Family: +1-555-XXX-1002  
   - Pediatric Care: +1-555-XXX-1003
```

#### 3. Create Contact Flow
Create a contact flow that calls your Bedrock Agent:

```json
{
  "Version": "2019-10-30",
  "StartAction": "12345678-1234-1234-1234-123456789012",
  "Actions": [
    {
      "Identifier": "12345678-1234-1234-1234-123456789012",
      "Type": "InvokeExternalResource",
      "Parameters": {
        "FunctionArn": "arn:aws:lambda:us-east-1:089580247707:function:bedrock-agent-connector",
        "TimeoutSeconds": 8
      },
      "Transitions": {
        "NextAction": "87654321-4321-4321-4321-210987654321",
        "Errors": [
          {
            "NextAction": "87654321-4321-4321-4321-210987654321",
            "ErrorType": "NoMatchingError"
          }
        ]
      }
    }
  ]
}
```

#### 4. Test Immediately
```bash
# Call your Connect phone numbers
# Each number will route to Bedrock Agent with DID context
```

---

### 🥈 Option 2: Twilio (Good Balance - Medium Setup)

**Why Choose This:**
- Quick setup (30 minutes)
- Programmable webhooks
- Good documentation
- Reasonable pricing (~$0.013/minute)

**Setup Steps:**

#### 1. Create Twilio Account
```bash
# Sign up at twilio.com
# Get Account SID and Auth Token
# Add $20 credit for testing
```

#### 2. Buy Phone Numbers
```bash
# Via Twilio Console or API
curl -X POST https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/IncomingPhoneNumbers.json \
  --data-urlencode "PhoneNumber=+15551234001" \
  --data-urlencode "VoiceUrl=https://your-webhook.com/voice/1001" \
  -u $ACCOUNT_SID:$AUTH_TOKEN

# Repeat for 1002 and 1003
```

#### 3. Create Webhook Lambda
```python
# Create Lambda function: twilio-bedrock-bridge
import json
import boto3
from twilio.twiml import VoiceResponse

def lambda_handler(event, context):
    # Extract DID from webhook URL
    did = event['pathParameters']['did']
    
    # Get caller input from Twilio
    speech_result = event.get('SpeechResult', '')
    
    # Call Bedrock Agent
    bedrock = boto3.client('bedrock-agent-runtime')
    response = bedrock.invoke_agent(
        agentId='S2MOVY5G8J',
        agentAliasId='XOOC4XVDXZ',
        sessionId=f"twilio-{did}-{event['CallSid']}",
        inputText=f"[DID: {did}] {speech_result}"
    )
    
    # Parse Bedrock response
    agent_text = parse_bedrock_response(response)
    
    # Create TwiML response
    twiml = VoiceResponse()
    twiml.say(agent_text, voice='alice')
    twiml.gather(input='speech', action=f'/voice/{did}', method='POST')
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/xml'},
        'body': str(twiml)
    }
```

#### 4. Test Your Numbers
```bash
# Call each Twilio number
# Verify DID routing and Bedrock integration
```

---

### 🥉 Option 3: SIP Trunk + FreeSWITCH (Most Control - Complex Setup)

**Why Choose This:**
- Complete control
- Lowest per-minute costs
- Custom features possible
- Learning experience

**Setup Steps:**

#### 1. Get SIP Trunk Provider
Popular providers:
- **Twilio Elastic SIP Trunking** (easiest)
- **Bandwidth.com** (good rates)
- **VoIP.ms** (budget-friendly)
- **Flowroute** (developer-friendly)

#### 2. Deploy FreeSWITCH Server
```bash
# Launch EC2 instance (t3.medium, Ubuntu 22.04)
# Open ports: 22, 5060, 5080, 16384-32768
# Assign Elastic IP

# Install FreeSWITCH
sudo apt update
sudo apt install -y gnupg2 wget lsb-release

# Add FreeSWITCH repository
wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | sudo apt-key add -
echo "deb https://files.freeswitch.org/repo/deb/debian-release/ `lsb_release -sc` main" | sudo tee /etc/apt/sources.list.d/freeswitch.list

sudo apt update
sudo apt install -y freeswitch-meta-all freeswitch-mod-lua

# Copy your configuration files
sudo cp -r freeswitch/conf/* /etc/freeswitch/
sudo cp -r freeswitch/scripts/* /usr/share/freeswitch/scripts/

# Start FreeSWITCH
sudo systemctl start freeswitch
sudo systemctl enable freeswitch
```

#### 3. Configure SIP Trunk
Update `/etc/freeswitch/sip_profiles/external.xml`:
```xml
<gateway name="your_provider">
  <param name="username" value="your_username"/>
  <param name="password" value="your_password"/>
  <param name="realm" value="sip.provider.com"/>
  <param name="proxy" value="sip.provider.com"/>
  <param name="register" value="true"/>
</gateway>
```

#### 4. Configure DIDs with Provider
Map your DIDs to your FreeSWITCH server:
- **1001** → your-server-ip:5080
- **1002** → your-server-ip:5080  
- **1003** → your-server-ip:5080

#### 5. Test Voice Calls
```bash
# Check FreeSWITCH status
sudo fs_cli -x "status"

# Monitor calls
sudo fs_cli -x "show calls"

# View logs
sudo tail -f /var/log/freeswitch/freeswitch.log
```

---

## 🧪 Quick Testing Options (No Setup Required)

### Option A: Use Existing Twilio Trial
```bash
# Sign up for Twilio trial (free $15 credit)
# Get a trial phone number instantly
# Create simple webhook that logs calls
# Test basic voice routing
```

### Option B: Use Amazon Connect Trial
```bash
# AWS Free Tier includes Connect usage
# Set up in 15 minutes
# Test with real phone calls immediately
```

### Option C: Use SIP Softphone
```bash
# Install softphone app (Zoiper, X-Lite)
# Connect to your FreeSWITCH server
# Test locally without phone charges
```

---

## 📞 Testing Checklist

### Pre-Test Setup
- [ ] Backend services running (test with `python3 scripts/test_phase5_backend.py`)
- [ ] AWS credentials configured
- [ ] Bedrock Agent accessible (Agent ID: S2MOVY5G8J)
- [ ] Phone numbers/DIDs configured

### Test Scenarios

#### 1. **Basic Connectivity Test**
```bash
Call: Your phone number
Expected: Greeting plays for correct clinic
Test: "Hello" → Should get clinic-specific greeting
```

#### 2. **Appointment Booking Flow**
```bash
Call: DID 1001 (Downtown Medical)
Say: "I need an appointment"
Expected: "I'd be happy to help you schedule an appointment. What day would work best for you?"

Say: "Tomorrow morning"
Expected: "Great! I have several slots available tomorrow morning. Would 9:30 AM work for you?"

Say: "Yes"
Expected: "Perfect! I'll book that appointment for you. Can I get your name and phone number?"

Say: "John Smith, 555-123-4567"
Expected: "Thank you! I've booked your appointment for tomorrow at 9:30 AM. Your confirmation number is DOWN-1218-XXX"
```

#### 3. **Multi-Tenant Isolation Test**
```bash
# Test each DID gets correct clinic greeting
Call 1001: Should hear "Downtown Medical Center"
Call 1002: Should hear "Westside Family Practice"  
Call 1003: Should hear "Pediatric Care Clinic"
```

#### 4. **Error Handling Test**
```bash
Say: "Gibberish words that make no sense"
Expected: "I understand you're looking for assistance. Could you tell me if you'd like to schedule an appointment..."
```

### Success Criteria
- [ ] All 3 DIDs route to correct clinics
- [ ] Speech recognition works clearly
- [ ] Appointment booking completes end-to-end
- [ ] Confirmation numbers generated
- [ ] Backend services receive requests
- [ ] No system errors in logs

---

## 🚀 Recommended Quick Start

**For immediate testing, I recommend Amazon Connect:**

1. **Sign up for AWS** (if not already done)
2. **Create Connect instance** (5 minutes)
3. **Claim phone number** (2 minutes)
4. **Create simple contact flow** (10 minutes)
5. **Call and test** (immediate)

**Total setup time: ~20 minutes**
**Cost: ~$0.02 per test call**

This gets you testing real voice calls with your Bedrock Agent integration immediately, without any server setup or complex configuration.

Would you like me to walk you through setting up Amazon Connect for immediate testing?