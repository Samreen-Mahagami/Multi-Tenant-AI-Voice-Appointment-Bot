# Phase 6: FreeSWITCH Voice Integration

## Overview
Integrate FreeSWITCH as the telephony engine to handle incoming voice calls and route them to our Bedrock Agent based on DID (Direct Inward Dialing).

## Architecture Integration

```
Incoming Call → FreeSWITCH → DID Routing → Bedrock Agent → Lambda Functions → Go Services
```

## FreeSWITCH Components Needed

### 1. **FreeSWITCH Server Setup**
- **SIP Trunk Configuration** for incoming calls
- **DID Routing Logic** (1001, 1002, 1003)
- **Audio Processing** for voice-to-text and text-to-voice
- **Session Management** for call handling

### 2. **Integration Points**

#### A. **DID-Based Call Routing**
```xml
<!-- FreeSWITCH Dialplan -->
<extension name="clinic_routing">
  <condition field="destination_number" expression="^(1001|1002|1003)$">
    <action application="set" data="tenant_did=$1"/>
    <action application="lua" data="bedrock_agent_handler.lua"/>
  </condition>
</extension>
```

#### B. **Bedrock Agent Integration**
- **Voice-to-Text**: Convert caller speech to text
- **Agent Processing**: Send text to Bedrock Agent with DID context
- **Text-to-Voice**: Convert agent response back to speech
- **Session Continuity**: Maintain conversation state

### 3. **Required FreeSWITCH Modules**
- `mod_lua` - For custom call logic
- `mod_http_cache` - For API calls to Bedrock
- `mod_json_cdr` - For call detail records
- `mod_polly` or `mod_tts_commandline` - For text-to-speech
- `mod_speech_utils` - For speech recognition

## Implementation Status

### ✅ **Configuration Complete**
- Dialplan configured for DID routing (1001, 1002, 1003)
- SIP profile ready for external trunk
- Lua scripts for Bedrock Agent integration
- Docker Compose setup prepared
- AWS Bedrock client implementation

### ⚠️ **Deployment Options**

#### Option A: Amazon Connect (Recommended)
- Managed voice infrastructure
- Native AWS integration
- No server management required
- Built-in Bedrock Agent support

#### Option B: FreeSWITCH on EC2
- Custom voice infrastructure
- Full control over configuration
- Requires server management
- Manual Bedrock integration

#### Option C: Twilio Integration
- Managed voice with webhooks
- Lambda bridge to Bedrock
- Pay-per-use pricing
- Quick deployment

### Step 2: Lua Script for Bedrock Integration
```lua
-- bedrock_agent_handler.lua
function bedrock_call_handler(session)
    local did = session:getVariable("tenant_did")
    
    -- Get tenant configuration
    local tenant_config = get_tenant_by_did(did)
    
    -- Play greeting
    session:speak(tenant_config.greeting)
    
    -- Start conversation loop
    while session:ready() do
        -- Get user speech
        local user_input = get_speech_input(session)
        
        -- Send to Bedrock Agent
        local agent_response = call_bedrock_agent(user_input, did, session_id)
        
        -- Speak response
        session:speak(agent_response)
        
        -- Check if call should end
        if should_end_call(agent_response) then
            break
        end
    end
end
```

### Step 3: API Integration Layer
```lua
-- api_integration.lua
function call_bedrock_agent(input_text, did, session_id)
    local http = require("socket.http")
    local json = require("json")
    
    local payload = {
        agentId = "S2MOVY5G8J",
        agentAliasId = "XOOC4XVDXZ",
        sessionId = session_id,
        inputText = "[DID: " .. did .. "] " .. input_text
    }
    
    -- Call AWS Bedrock Agent Runtime API
    local response = http.request{
        url = "https://bedrock-agent-runtime.us-east-1.amazonaws.com/agents/S2MOVY5G8J/agentAliases/XOOC4XVDXZ/sessions/" .. session_id .. "/text",
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Authorization"] = get_aws_auth_header()
        },
        source = json.encode(payload)
    }
    
    return parse_bedrock_response(response)
end
```

## Configuration Files

### 1. **SIP Profile** (`conf/sip_profiles/external.xml`)
```xml
<profile name="external">
  <gateways>
    <gateway name="clinic_trunk">
      <param name="username" value="clinic_user"/>
      <param name="password" value="clinic_pass"/>
      <param name="proxy" value="sip.provider.com"/>
      <param name="register" value="true"/>
    </gateway>
  </gateways>
  
  <settings>
    <param name="context" value="public"/>
    <param name="rtp-ip" value="auto"/>
    <param name="sip-ip" value="auto"/>
  </settings>
</profile>
```

### 2. **Dialplan** (`conf/dialplan/default.xml`)
```xml
<context name="public">
  <extension name="clinic_dids">
    <condition field="destination_number" expression="^(1001)$">
      <action application="set" data="tenant_did=1001"/>
      <action application="set" data="clinic_name=Downtown Medical Center"/>
      <action application="lua" data="bedrock_agent_handler.lua"/>
    </condition>
    
    <condition field="destination_number" expression="^(1002)$">
      <action application="set" data="tenant_did=1002"/>
      <action application="set" data="clinic_name=Westside Family Practice"/>
      <action application="lua" data="bedrock_agent_handler.lua"/>
    </condition>
    
    <condition field="destination_number" expression="^(1003)$">
      <action application="set" data="tenant_did=1003"/>
      <action application="set" data="clinic_name=Pediatric Care Clinic"/>
      <action application="lua" data="bedrock_agent_handler.lua"/>
    </condition>
  </extension>
</context>
```

## Voice Processing Pipeline

### 1. **Speech-to-Text (STT)**
```lua
function get_speech_input(session)
    session:execute("detect_speech", "pocketsphinx default default")
    session:execute("play_and_detect_speech", "silence_stream://2000 detect:speech default")
    
    local speech_result = session:getVariable("detect_speech_result")
    return speech_result
end
```

### 2. **Text-to-Speech (TTS)**
```lua
function speak_response(session, text, voice_id)
    -- Use Amazon Polly for consistent voice
    local polly_params = "polly://" .. voice_id .. "/" .. text
    session:speak(polly_params)
end
```

## Deployment Architecture

### Option A: **EC2 Instance**
```bash
# Launch EC2 instance
# Install FreeSWITCH
# Configure SIP trunks
# Deploy Lua scripts
# Set up monitoring
```

### Option B: **Docker Container**
```dockerfile
FROM freeswitch/freeswitch:latest

COPY conf/ /etc/freeswitch/
COPY scripts/ /usr/share/freeswitch/scripts/

EXPOSE 5060/udp 5080/udp
EXPOSE 16384-32768/udp

CMD ["freeswitch", "-nonat", "-c"]
```

## Integration Testing

### 1. **SIP Call Testing**
- Test inbound calls to each DID
- Verify audio quality
- Test call routing logic

### 2. **Bedrock Integration Testing**
- Test voice-to-text accuracy
- Verify agent responses
- Test appointment booking flow

### 3. **End-to-End Testing**
- Complete appointment booking via voice call
- Multi-tenant isolation testing
- Error handling and fallback scenarios

## Monitoring & Logging

### 1. **Call Detail Records (CDR)**
```json
{
  "call_id": "uuid",
  "did": "1001",
  "tenant": "downtown_medical",
  "start_time": "2025-12-18T10:00:00Z",
  "end_time": "2025-12-18T10:05:30Z",
  "duration": 330,
  "appointment_booked": true,
  "confirmation_ref": "DOWN-1218-456"
}
```

### 2. **Performance Metrics**
- Call success rate
- Average call duration
- Speech recognition accuracy
- Appointment booking conversion rate

## Security Considerations

### 1. **SIP Security**
- TLS encryption for SIP signaling
- SRTP for media encryption
- IP whitelisting for SIP trunks

### 2. **API Security**
- AWS IAM roles for Bedrock access
- API rate limiting
- Request validation

## Next Steps After Phase 6

1. **Production Deployment**
   - Set up SIP trunks with telecom provider
   - Configure production FreeSWITCH server
   - Deploy monitoring and alerting

2. **Advanced Features**
   - Call recording and compliance
   - Real-time analytics dashboard
   - Advanced speech recognition tuning

3. **Scaling**
   - Load balancing for multiple FreeSWITCH instances
   - Geographic distribution
   - High availability setup