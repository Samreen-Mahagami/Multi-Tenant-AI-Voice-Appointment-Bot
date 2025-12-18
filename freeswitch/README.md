# FreeSWITCH Voice Integration for Multi-Tenant AI Voice Appointment Bot

## Overview

This directory contains the FreeSWITCH configuration for handling real voice calls and integrating with the AWS Bedrock Agent for appointment booking.

## Architecture

```
Incoming Call → FreeSWITCH (SIP/RTP) → DID Routing → Lua Scripts → AWS Bedrock Agent → Go Services
```

## Current Status

✅ **Configuration Files Ready**:
- Dialplan with DID routing (1001, 1002, 1003)
- SIP profile for external trunk
- Lua scripts for Bedrock integration
- Docker Compose setup

⚠️ **Deployment Options**:

### Option 1: Use Amazon Connect (Recommended for Production)
Amazon Connect provides managed voice infrastructure with built-in AWS integration:
- No FreeSWITCH server management needed
- Native Bedrock Agent integration
- Automatic scaling and high availability
- Pay-per-use pricing

**Setup Steps**:
1. Create Amazon Connect instance
2. Configure phone numbers for each clinic
3. Create contact flows that invoke Bedrock Agent
4. Map DIDs to contact flows

### Option 2: Deploy FreeSWITCH on EC2
For custom voice infrastructure control:

**Prerequisites**:
- EC2 instance (t3.medium or larger)
- Public IP address
- SIP trunk provider account
- Open ports: 5060/5080 (SIP), 16384-32768 (RTP)

**Installation**:
```bash
# On Ubuntu 22.04 LTS
sudo apt-get update
sudo apt-get install -y gnupg2 wget

# Add FreeSWITCH repository
wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | sudo apt-key add -
echo "deb https://files.freeswitch.org/repo/deb/debian-release/ `lsb_release -sc` main" | sudo tee /etc/apt/sources.list.d/freeswitch.list

# Install FreeSWITCH
sudo apt-get update
sudo apt-get install -y freeswitch-meta-all

# Copy configuration files
sudo cp -r conf/* /etc/freeswitch/
sudo cp -r scripts/* /usr/share/freeswitch/scripts/

# Start FreeSWITCH
sudo systemctl start freeswitch
sudo systemctl enable freeswitch
```

### Option 3: Use Twilio with Bedrock Integration
Twilio provides voice infrastructure with programmable webhooks:
- Purchase phone numbers for each clinic
- Configure TwiML webhooks
- Create Lambda function to bridge Twilio ↔ Bedrock Agent
- Map phone numbers to DIDs

## Configuration Files

### 1. Dialplan (`conf/dialplan/default.xml`)
Routes incoming calls based on DID:
- **1001** → Downtown Medical Center
- **1002** → Westside Family Practice
- **1003** → Pediatric Care Clinic

### 2. SIP Profile (`conf/sip_profiles/external.xml`)
Configures SIP trunk for incoming calls from provider.

### 3. Lua Scripts
- `bedrock_agent_handler.lua` - Main call handler
- `aws_bedrock_client.lua` - AWS Bedrock API client

## Testing Without FreeSWITCH

You can test the voice flow logic without deploying FreeSWITCH:

```bash
# Test backend services
python3 scripts/test_phase5_backend.py

# Simulate voice conversation
python3 scripts/test_phase5_voice.py
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# SIP Trunk (if using FreeSWITCH)
SIP_TRUNK_USERNAME=your_username
SIP_TRUNK_PASSWORD=your_password
SIP_TRUNK_REALM=sip.provider.com

# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Service URLs (already configured)
TENANT_CONFIG_URL=https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod
APPOINTMENT_SERVICE_URL=https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod
```

## Voice Flow Example

1. **Caller dials** 1-555-123-1001 (Downtown Medical)
2. **FreeSWITCH receives** call, routes to DID 1001
3. **Lua script** plays greeting: "Hello, thank you for calling Downtown Medical Center..."
4. **Speech recognition** captures: "I need an appointment"
5. **Bedrock Agent** processes request with DID context
6. **Agent responds**: "I'd be happy to help you schedule an appointment..."
7. **Conversation continues** until appointment is booked
8. **Confirmation** provided: "Your confirmation number is DOWN-1218-456"

## Production Deployment Checklist

- [ ] Choose voice infrastructure (Amazon Connect, FreeSWITCH, or Twilio)
- [ ] Configure phone numbers/DIDs for each clinic
- [ ] Set up SIP trunks or voice provider
- [ ] Configure firewall rules for voice traffic
- [ ] Deploy and test voice routing
- [ ] Configure AWS credentials for Bedrock access
- [ ] Test end-to-end voice calls
- [ ] Set up call recording (if required for compliance)
- [ ] Configure monitoring and alerting
- [ ] Document emergency fallback procedures

## Monitoring

Key metrics to track:
- Call success rate
- Average call duration
- Speech recognition accuracy
- Appointment booking conversion rate
- System errors and failures

## Security Considerations

1. **SIP Security**:
   - Use TLS for SIP signaling
   - Enable SRTP for media encryption
   - IP whitelist for SIP trunks

2. **AWS Security**:
   - Use IAM roles with minimal permissions
   - Rotate AWS credentials regularly
   - Enable CloudTrail logging

3. **Data Privacy**:
   - Comply with HIPAA if handling PHI
   - Secure call recordings
   - Implement data retention policies

## Support

For issues or questions:
1. Check FreeSWITCH logs: `/var/log/freeswitch/freeswitch.log`
2. Test backend services: `python3 scripts/test_phase5_backend.py`
3. Review Bedrock Agent logs in CloudWatch
4. Check Lambda function logs

## Next Steps

1. **Choose your voice infrastructure** (Amazon Connect recommended)
2. **Configure phone numbers** for the 3 clinics
3. **Test voice integration** with sample calls
4. **Deploy to production** with monitoring
5. **Train staff** on the new system

## Resources

- [Amazon Connect Documentation](https://docs.aws.amazon.com/connect/)
- [FreeSWITCH Documentation](https://freeswitch.org/confluence/)
- [AWS Bedrock Agent Runtime API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_InvokeAgent.html)
- [Twilio Voice Documentation](https://www.twilio.com/docs/voice)