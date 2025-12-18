# AISPL Account Solution: Real Voice Bot Setup

## The Problem

Your AWS account is provided by **AISPL (Amazon Internet Services Private Limited)**, which has restrictions on certain AWS services including:
- ❌ Amazon Connect (cannot create instances)
- ❌ Some telephony services
- ❌ Certain regional services

## The Solution: Twilio Integration

Instead of Amazon Connect, we'll use **Twilio** which works perfectly with AISPL accounts and gives you the same real voice capabilities.

## Why Twilio is Better for AISPL Accounts

✅ **Works with any AWS account** (including AISPL)  
✅ **Easier setup** (no complex AWS service dependencies)  
✅ **Better pricing** (~$0.02 per call vs ~$0.05 with Connect)  
✅ **More reliable** (dedicated telephony infrastructure)  
✅ **Global phone numbers** (not restricted by AWS regions)  

## Quick Setup (15 minutes)

### Step 1: Set Up Twilio Webhook Infrastructure

```bash
# Run the Twilio setup script
python3 scripts/setup_twilio_voice.py
```

This creates:
- **Lambda webhook function** to handle Twilio calls
- **API Gateway endpoint** for Twilio to call
- **IAM roles and permissions** for integration

### Step 2: Get Your Twilio Phone Number

1. **Sign up for Twilio** (free $15 credit)
   ```
   https://www.twilio.com/try-twilio
   ```

2. **Verify your phone number**
   - Enter your real phone number
   - Receive SMS verification code

3. **Buy a phone number**
   - Go to Phone Numbers → Manage → Buy a number
   - Choose any US number (~$1/month)
   - Purchase it

### Step 3: Configure Your Phone Number

1. **Go to Active Numbers**
   ```
   Twilio Console → Phone Numbers → Manage → Active numbers
   ```

2. **Click on your purchased number**

3. **Configure Voice webhook**
   - Webhook URL: `https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/voice`
   - HTTP Method: `POST`
   - Save configuration

### Step 4: Test Your Voice Bot

```bash
# Call your Twilio phone number
# Say: "I need an appointment"
# Bot responds with voice!
```

## Complete Voice Flow

```
Your Voice Call → Twilio → API Gateway → Lambda Webhook → Voice Processor → Bedrock Agent → Response
```

### What Happens:

1. **You call** the Twilio phone number
2. **Twilio captures** your speech (speech-to-text)
3. **Webhook Lambda** receives the text
4. **Voice Processor** calls Bedrock Agent
5. **Bedrock Agent** processes appointment request
6. **Response** converted to speech (text-to-speech)
7. **You hear** the bot's voice response

## Architecture Comparison

### ❌ Amazon Connect (Blocked for AISPL)
```
Phone → Connect → Lambda → Bedrock → Response
```
**Issues**: Cannot create Connect instances with AISPL accounts

### ✅ Twilio Solution (Works with AISPL)
```
Phone → Twilio → API Gateway → Lambda → Bedrock → Response
```
**Benefits**: No AWS service restrictions, works globally

## Cost Comparison

### Amazon Connect (if it worked)
- Connect usage: $0.018/minute
- Lambda: $0.0000002/request
- Transcribe: $0.024/minute
- Polly: $0.016/1M characters
- **Total**: ~$0.05/call

### Twilio Solution
- Phone number: $1/month
- Incoming calls: $0.0085/minute
- Lambda: $0.0000002/request
- Polly: $0.016/1M characters
- **Total**: ~$0.02/call (60% cheaper!)

## Testing Your Setup

### Test 1: Basic Call
```bash
# Call your Twilio number
# Expected: "Hello! Welcome to our AI voice appointment bot..."
```

### Test 2: Appointment Booking
```bash
# Say: "I need an appointment"
# Expected: "I'd be happy to help you schedule an appointment..."

# Say: "Tomorrow morning"
# Expected: "Great! I have several slots available..."

# Continue the conversation
```

### Test 3: Multi-Tenant (Optional)
If you want different numbers for different clinics:
1. Buy 3 Twilio numbers
2. Configure each with the same webhook
3. The system will detect which number was called

## Troubleshooting

### Issue: Webhook not receiving calls
**Solution**: 
- Check API Gateway URL is correct
- Verify Twilio webhook configuration
- Check Lambda logs in CloudWatch

### Issue: No voice response
**Solution**:
- Check voice processor Lambda logs
- Verify Bedrock Agent is working
- Test with `python3 scripts/simulate_phone_call.py`

### Issue: Poor speech recognition
**Solution**:
- Speak clearly and slowly
- Use a good phone connection
- Twilio's speech recognition is very good by default

## Advanced Configuration

### Custom Voices per Clinic
You can modify the webhook to use different voices:

```python
# In the webhook Lambda
clinic_voices = {
    '1001': 'alice',    # Downtown Medical
    '1002': 'man',      # Westside Family  
    '1003': 'woman'     # Pediatric Care
}
```

### Call Recording
Enable call recording in Twilio:
```xml
<Record action="/recording" />
```

### Call Analytics
Twilio provides detailed call analytics:
- Call duration
- Speech recognition accuracy
- Call quality metrics

## Production Deployment

### Security
- Enable HTTPS only
- Add API key authentication
- Whitelist Twilio IP addresses

### Scaling
- Twilio handles unlimited concurrent calls
- Lambda automatically scales
- No infrastructure management needed

### Monitoring
- CloudWatch for Lambda metrics
- Twilio Console for call analytics
- Set up alerts for failed calls

## Summary

**The AISPL account restriction is completely solved with Twilio:**

✅ **Real phone numbers** you can call  
✅ **Speech-to-text** conversion  
✅ **AI processing** with Bedrock Agent  
✅ **Text-to-speech** responses  
✅ **Multi-tenant** support  
✅ **Production ready** infrastructure  
✅ **Lower costs** than Amazon Connect  
✅ **No AWS service restrictions**  

Your voice bot will work exactly the same as if you had Amazon Connect, but with better reliability and lower costs!