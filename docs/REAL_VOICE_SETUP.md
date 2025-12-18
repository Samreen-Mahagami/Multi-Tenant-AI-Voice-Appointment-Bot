# Real Voice Bot Setup Guide

## Overview

This guide shows you how to set up a **real voice-based bot** where you can:
- **Call a phone number** and speak
- **Bot listens** to your voice (Speech-to-Text with Amazon Transcribe)
- **Bot processes** your request (AWS Bedrock Agent)
- **Bot responds** with voice (Text-to-Speech with Amazon Polly)

## Architecture

```
Your Voice → Phone Call → Amazon Connect → Lambda (Transcribe) → Bedrock Agent → Lambda (Polly) → Voice Response
```

## Components Used

1. **Amazon Transcribe** - Converts your speech to text
2. **Amazon Polly** - Converts bot responses to speech
3. **AWS Bedrock Agent** - Processes appointment requests
4. **Amazon Connect** - Handles phone calls
5. **AWS Lambda** - Orchestrates the voice processing

## Quick Setup (30 minutes)

### Step 1: Deploy Voice Processing Lambda

```bash
# Deploy the voice stack
cd infrastructure
npm run build
cdk deploy IvrVoiceStack

# Note the Lambda function ARN from output
```

### Step 2: Create S3 Bucket for Audio

```bash
# Create bucket for audio processing
aws s3 mb s3://clinic-voice-processing-$(aws sts get-caller-identity --query Account --output text)

# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name IvrVoiceStack-VoiceProcessorFunction \
  --environment Variables={S3_BUCKET=clinic-voice-processing-YOUR_ACCOUNT_ID}
```

### Step 3: Set Up Amazon Connect

#### Option A: Using AWS Console (Easiest)

1. **Go to Amazon Connect Console**
   ```
   https://console.aws.amazon.com/connect/
   ```

2. **Create Instance**
   - Click "Add an instance"
   - Instance alias: `clinic-voice-bot`
   - Identity management: "Store users within Amazon Connect"
   - Create administrator
   - Enable telephony

3. **Claim Phone Numbers**
   - Go to "Phone numbers" → "Claim a number"
   - Choose toll-free or DID
   - Claim 3 numbers (one per clinic)
   - Note the numbers:
     - Downtown Medical: +1-XXX-XXX-1001
     - Westside Family: +1-XXX-XXX-1002
     - Pediatric Care: +1-XXX-XXX-1003

4. **Create Contact Flow**
   
   Create a new contact flow with these blocks:

   ```
   [Start] 
     ↓
   [Set logging behavior] - Enable CloudWatch logs
     ↓
   [Get customer input] - Speech recognition enabled
     ↓
   [Invoke AWS Lambda function] - Select voice-processor function
     ↓
   [Play prompt] - Use Lambda response
     ↓
   [Check contact attributes] - If conversation continues, loop back
     ↓
   [Disconnect]
   ```

   **Detailed Contact Flow Configuration:**

   a. **Get customer input block:**
   - Input type: Speech
   - Amazon Lex bot: None
   - Interpret as: Text
   - Store customer input in: `$.Attributes.userInput`

   b. **Invoke Lambda function block:**
   - Function ARN: (Your voice-processor Lambda ARN)
   - Timeout: 30 seconds
   - Parameters to send:
     - `userInput`: `$.Attributes.userInput`
     - `did`: `$.CustomerEndpoint.Address` (last 4 digits)
     - `contactId`: `$.ContactId`

   c. **Play prompt block:**
   - Prompt type: Text-to-speech
   - Text: `$.External.agentResponse`
   - Voice: Joanna (or from Lambda response)

5. **Associate Phone Numbers with Contact Flow**
   - Go to each phone number
   - Associate with your contact flow
   - Save

#### Option B: Using CLI/Script

```bash
# Run the automated setup script
python3 scripts/setup_amazon_connect.py
```

### Step 4: Test Your Voice Bot

#### Test 1: Call the Phone Number

```bash
# Call your Connect phone number
# Example: +1-800-XXX-1001

# Say: "I need an appointment"
# Bot will respond with voice
```

#### Test 2: Test Locally (Without Phone)

```bash
# Test the voice processing Lambda directly
python3 scripts/voice_client.py

# This will simulate voice interactions
```

## Voice Processing Flow

### 1. Incoming Call
```
User calls → Amazon Connect answers → Plays greeting
```

### 2. Speech Recognition
```
User speaks → Amazon Transcribe converts to text
Example: "I need an appointment tomorrow" → Text
```

### 3. AI Processing
```
Text → Bedrock Agent processes → Generates response
Example: "I'd be happy to help you schedule an appointment..."
```

### 4. Speech Synthesis
```
Response text → Amazon Polly → Voice audio
Voice: Joanna (Downtown), Matthew (Westside), Salli (Pediatric)
```

### 5. Play Response
```
Audio → Amazon Connect plays to caller → User hears response
```

## Voice Configuration

### Clinic-Specific Voices

Each clinic has its own voice personality:

```python
CLINIC_VOICES = {
    '1001': {  # Downtown Medical Center
        'voice_id': 'Joanna',
        'engine': 'neural',
        'language': 'en-US'
    },
    '1002': {  # Westside Family Practice
        'voice_id': 'Matthew',
        'engine': 'neural',
        'language': 'en-US'
    },
    '1003': {  # Pediatric Care Clinic
        'voice_id': 'Salli',
        'engine': 'neural',
        'language': 'en-US'
    }
}
```

### Available Polly Voices

- **Joanna** - Professional female voice
- **Matthew** - Professional male voice
- **Salli** - Friendly female voice
- **Joey** - Young male voice
- **Ivy** - Child-friendly female voice

## Testing Scenarios

### Scenario 1: Book Appointment

```
You: "Hello, I need to schedule an appointment"
Bot: "I'd be happy to help you schedule an appointment. What day would work best for you?"

You: "Tomorrow morning"
Bot: "Great! I have several slots available tomorrow morning. Would 9:30 AM work for you?"

You: "Yes, that works"
Bot: "Perfect! I'll book that appointment for you. Can I get your name and phone number?"

You: "John Smith, 555-123-4567"
Bot: "Thank you! I've booked your appointment for tomorrow at 9:30 AM. Your confirmation number is DOWN-1218-456. Is there anything else I can help you with?"

You: "No, thank you"
Bot: "You're welcome! Thank you for calling Downtown Medical Center. Have a great day!"
```

### Scenario 2: Check Hours

```
You: "What are your hours?"
Bot: "We're open Monday through Friday from 9 AM to 5 PM. Is there anything else I can help you with?"
```

### Scenario 3: Cancel Appointment

```
You: "I need to cancel my appointment"
Bot: "I can help you with that. Can you provide me with your confirmation number?"

You: "DOWN-1218-456"
Bot: "I've found your appointment for tomorrow at 9:30 AM. Would you like me to cancel it?"

You: "Yes"
Bot: "Your appointment has been cancelled. Would you like to reschedule for a different time?"
```

## Monitoring & Debugging

### View Call Logs

```bash
# CloudWatch Logs for Connect
aws logs tail /aws/connect/clinic-voice-bot --follow

# Lambda function logs
aws logs tail /aws/lambda/IvrVoiceStack-VoiceProcessorFunction --follow
```

### Test Voice Processing

```bash
# Test Transcribe
aws transcribe start-transcription-job \
  --transcription-job-name test-job \
  --media MediaFileUri=s3://your-bucket/test-audio.wav \
  --language-code en-US

# Test Polly
aws polly synthesize-speech \
  --text "Hello, this is a test" \
  --voice-id Joanna \
  --output-format mp3 \
  test-output.mp3
```

## Costs

### Estimated Costs per Call

- **Amazon Connect**: $0.018/minute
- **Amazon Transcribe**: $0.024/minute
- **Amazon Polly**: $0.016 per 1M characters (~$0.001 per call)
- **AWS Lambda**: $0.0000002 per request
- **Total**: ~$0.05 per 1-minute call

### Monthly Estimates

- **100 calls/month**: ~$5
- **1,000 calls/month**: ~$50
- **10,000 calls/month**: ~$500

## Troubleshooting

### Issue: No audio response

**Solution:**
- Check S3 bucket permissions
- Verify Polly has correct IAM permissions
- Check Lambda logs for errors

### Issue: Speech not recognized

**Solution:**
- Speak clearly and slowly
- Check microphone quality
- Verify Transcribe language settings
- Review Connect input settings

### Issue: Wrong clinic routing

**Solution:**
- Verify DID mapping in contact flow
- Check phone number configuration
- Review Lambda DID extraction logic

## Production Checklist

- [ ] S3 bucket created for audio processing
- [ ] Lambda function deployed with correct permissions
- [ ] Amazon Connect instance configured
- [ ] Phone numbers claimed and associated
- [ ] Contact flows created and tested
- [ ] Voice quality tested on real calls
- [ ] Error handling tested
- [ ] Monitoring and alerts configured
- [ ] Call recording enabled (if required)
- [ ] HIPAA compliance reviewed (if handling PHI)

## Next Steps

1. **Test with real calls** - Call each phone number and test the flow
2. **Optimize voice quality** - Adjust Polly settings for better audio
3. **Add call recording** - Enable recording for quality assurance
4. **Set up monitoring** - Configure CloudWatch alarms
5. **Train staff** - Document the system for your team

## Support

For issues:
1. Check Lambda logs in CloudWatch
2. Review Connect contact flow logs
3. Test individual components (Transcribe, Polly, Bedrock)
4. Verify IAM permissions

## Resources

- [Amazon Connect Documentation](https://docs.aws.amazon.com/connect/)
- [Amazon Transcribe Documentation](https://docs.aws.amazon.com/transcribe/)
- [Amazon Polly Documentation](https://docs.aws.amazon.com/polly/)
- [AWS Bedrock Agent Documentation](https://docs.aws.amazon.com/bedrock/)