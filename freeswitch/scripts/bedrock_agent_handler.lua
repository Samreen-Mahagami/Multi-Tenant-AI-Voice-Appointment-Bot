--[[
  Multi-Tenant AI Voice Appointment Bot - FreeSWITCH Bedrock Agent Handler
  Handles voice calls and integrates with AWS Bedrock Agent for appointment booking
]]--

-- Load required modules
local json = require("json")
local http = require("socket.http")
local ltn12 = require("ltn12")

-- Load AWS Bedrock client
local BedrockClient = require("aws_bedrock_client")

-- AWS Configuration
local AWS_REGION = "us-east-1"
local BEDROCK_AGENT_ID = "S2MOVY5G8J"
local BEDROCK_AGENT_ALIAS_ID = "XOOC4XVDXZ"

-- Service URLs
local TENANT_CONFIG_URL = "https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod"
local APPOINTMENT_SERVICE_URL = "https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod"

-- Initialize Bedrock client
local bedrock_client = BedrockClient:new(AWS_REGION, BEDROCK_AGENT_ID, BEDROCK_AGENT_ALIAS_ID)

-- Main call handler function
function bedrock_call_handler(session)
    -- Get call variables
    local tenant_did = session:getVariable("tenant_did")
    local tenant_name = session:getVariable("tenant_name")
    local clinic_name = session:getVariable("clinic_name")
    local greeting = session:getVariable("greeting")
    local polly_voice = session:getVariable("polly_voice")
    
    -- Generate unique session ID for this call
    local session_id = "fs-" .. tenant_did .. "-" .. os.time() .. "-" .. math.random(1000, 9999)
    
    freeswitch.consoleLog("INFO", "Starting call for " .. clinic_name .. " (DID: " .. tenant_did .. ")")
    freeswitch.consoleLog("INFO", "Session ID: " .. session_id)
    
    -- Verify tenant configuration
    local tenant_config = get_tenant_config(tenant_did)
    if not tenant_config then
        freeswitch.consoleLog("ERROR", "Failed to get tenant config for DID: " .. tenant_did)
        session:speak("I'm sorry, but there seems to be a system error. Please try calling again later.")
        session:hangup()
        return
    end
    
    -- Play initial greeting
    speak_text(session, greeting, polly_voice)
    
    -- Initialize conversation state
    local conversation_active = true
    local max_silence_count = 3
    local silence_count = 0
    local max_conversation_time = 600 -- 10 minutes max
    local conversation_start = os.time()
    
    -- Main conversation loop
    while session:ready() and conversation_active do
        -- Check conversation timeout
        if os.time() - conversation_start > max_conversation_time then
            speak_text(session, "I'm sorry, but our conversation has reached the maximum time limit. Please call back if you need further assistance.", polly_voice)
            break
        end
        
        -- Get user input via speech recognition
        local user_input = get_speech_input(session)
        
        if user_input and user_input ~= "" then
            silence_count = 0
            freeswitch.consoleLog("INFO", "User said: " .. user_input)
            
            -- Send to Bedrock Agent with DID context
            local agent_response = call_bedrock_agent(user_input, tenant_did, session_id)
            
            if agent_response then
                freeswitch.consoleLog("INFO", "Agent response: " .. agent_response)
                
                -- Speak the agent's response
                speak_text(session, agent_response, polly_voice)
                
                -- Check if conversation should end
                if should_end_conversation(agent_response) then
                    conversation_active = false
                end
            else
                -- Error handling
                speak_text(session, "I'm sorry, I'm having trouble processing your request right now. Let me transfer you to a human representative.", polly_voice)
                -- Here you would implement transfer logic
                conversation_active = false
            end
        else
            -- Handle silence or no input
            silence_count = silence_count + 1
            freeswitch.consoleLog("INFO", "No input detected, silence count: " .. silence_count)
            
            if silence_count >= max_silence_count then
                speak_text(session, "I haven't heard from you in a while. If you need assistance, please call back. Have a great day!", polly_voice)
                conversation_active = false
            else
                speak_text(session, "I'm sorry, I didn't catch that. Could you please repeat what you said?", polly_voice)
            end
        end
    end
    
    -- End call gracefully
    freeswitch.consoleLog("INFO", "Ending call for session: " .. session_id)
    session:sleep(1000)
    session:hangup()
end

-- Get tenant configuration from our service
function get_tenant_config(did)
    local url = TENANT_CONFIG_URL .. "/v1/tenants/resolve?did=" .. did
    
    local response_body = {}
    local result, status = http.request{
        url = url,
        method = "GET",
        headers = {
            ["Content-Type"] = "application/json"
        },
        sink = ltn12.sink.table(response_body)
    }
    
    if status == 200 then
        local response_text = table.concat(response_body)
        local success, tenant_data = pcall(json.decode, response_text)
        if success then
            return tenant_data
        end
    end
    
    freeswitch.consoleLog("ERROR", "Failed to get tenant config for DID: " .. did .. " (Status: " .. tostring(status) .. ")")
    return nil
end

-- Call AWS Bedrock Agent
function call_bedrock_agent(input_text, did, session_id)
    freeswitch.consoleLog("INFO", "Calling Bedrock Agent for DID: " .. did)
    
    -- Use the Bedrock client to get response
    local response = bedrock_client:get_response(session_id, input_text, did)
    
    if response then
        return response
    else
        -- Ultimate fallback
        return "I'm sorry, I'm having trouble processing your request right now. Let me transfer you to a human representative."
    end
end

-- Speech-to-text function
function get_speech_input(session)
    -- Configure speech detection
    session:execute("detect_speech", "pocketsphinx default default")
    
    -- Play silence and detect speech
    session:execute("play_and_detect_speech", "silence_stream://5000 detect:speech default")
    
    -- Get the result
    local speech_result = session:getVariable("detect_speech_result")
    
    -- Clean up
    session:execute("detect_speech", "stop")
    
    return speech_result
end

-- Text-to-speech function
function speak_text(session, text, voice_id)
    if not text or text == "" then
        return
    end
    
    -- Use FreeSWITCH's built-in TTS or integrate with Amazon Polly
    -- For now, using FreeSWITCH's speak application
    session:speak(text)
    
    -- Alternative: Use Polly (requires mod_polly or custom implementation)
    -- local polly_url = "polly://" .. voice_id .. "/" .. text
    -- session:speak(polly_url)
end

-- Check if conversation should end
function should_end_conversation(response)
    local response_lower = string.lower(response)
    return string.find(response_lower, "goodbye") or 
           string.find(response_lower, "have a great day") or
           string.find(response_lower, "thank you for calling")
end

-- Log call details for monitoring
function log_call_details(session_id, tenant_did, duration, outcome)
    local call_log = {
        session_id = session_id,
        tenant_did = tenant_did,
        duration = duration,
        outcome = outcome,
        timestamp = os.date("%Y-%m-%d %H:%M:%S")
    }
    
    freeswitch.consoleLog("INFO", "Call completed: " .. json.encode(call_log))
end

-- Main entry point - called by FreeSWITCH
if session then
    bedrock_call_handler(session)
end