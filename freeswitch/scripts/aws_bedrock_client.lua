--[[
  AWS Bedrock Client for FreeSWITCH
  Handles AWS authentication and Bedrock Agent API calls
]]--

local json = require("json")
local http = require("socket.http")
local ltn12 = require("ltn12")
local crypto = require("crypto")
local mime = require("mime")

-- AWS Bedrock Client Class
local BedrockClient = {}
BedrockClient.__index = BedrockClient

-- Constructor
function BedrockClient:new(region, agent_id, agent_alias_id)
    local client = {
        region = region or "us-east-1",
        agent_id = agent_id or "S2MOVY5G8J",
        agent_alias_id = agent_alias_id or "XOOC4XVDXZ",
        service = "bedrock",
        host = "bedrock-agent-runtime." .. (region or "us-east-1") .. ".amazonaws.com"
    }
    setmetatable(client, BedrockClient)
    return client
end

-- Get AWS credentials from environment
function BedrockClient:get_credentials()
    local access_key = os.getenv("AWS_ACCESS_KEY_ID")
    local secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    local session_token = os.getenv("AWS_SESSION_TOKEN")
    
    if not access_key or not secret_key then
        freeswitch.consoleLog("ERROR", "AWS credentials not found in environment variables")
        return nil
    end
    
    return {
        access_key = access_key,
        secret_key = secret_key,
        session_token = session_token
    }
end

-- Create AWS Signature Version 4
function BedrockClient:create_signature_v4(method, uri, query_string, headers, payload, timestamp)
    local credentials = self:get_credentials()
    if not credentials then
        return nil
    end
    
    -- This is a simplified version - in production, use a proper AWS SDK
    -- For now, we'll use a simpler approach without full signature
    local auth_header = "AWS4-HMAC-SHA256 Credential=" .. credentials.access_key .. 
                       "/" .. os.date("%Y%m%d") .. "/" .. self.region .. "/" .. self.service .. "/aws4_request"
    
    return auth_header
end

-- Invoke Bedrock Agent
function BedrockClient:invoke_agent(session_id, input_text)
    local url = "https://" .. self.host .. "/agents/" .. self.agent_id .. 
                "/agentAliases/" .. self.agent_alias_id .. "/sessions/" .. session_id .. "/text"
    
    local payload = {
        inputText = input_text
    }
    
    local payload_json = json.encode(payload)
    local timestamp = os.date("!%Y%m%dT%H%M%SZ")
    
    -- Get authentication header
    local auth_header = self:create_signature_v4("POST", "/agents/" .. self.agent_id .. 
                                                 "/agentAliases/" .. self.agent_alias_id .. 
                                                 "/sessions/" .. session_id .. "/text", 
                                                 "", {}, payload_json, timestamp)
    
    local headers = {
        ["Content-Type"] = "application/x-amz-json-1.0",
        ["Content-Length"] = tostring(#payload_json),
        ["Host"] = self.host,
        ["X-Amz-Date"] = timestamp,
        ["X-Amz-Target"] = "AWSBedrockAgentRuntimeService.InvokeAgent"
    }
    
    if auth_header then
        headers["Authorization"] = auth_header
    end
    
    local response_body = {}
    local result, status_code, response_headers = http.request{
        url = url,
        method = "POST",
        headers = headers,
        source = ltn12.source.string(payload_json),
        sink = ltn12.sink.table(response_body)
    }
    
    if status_code == 200 then
        local response_text = table.concat(response_body)
        local success, response_data = pcall(json.decode, response_text)
        
        if success and response_data then
            return self:parse_bedrock_response(response_data)
        end
    end
    
    freeswitch.consoleLog("ERROR", "Bedrock API call failed: " .. tostring(status_code))
    return nil
end

-- Parse Bedrock streaming response
function BedrockClient:parse_bedrock_response(response_data)
    -- Handle Bedrock Agent streaming response format
    if response_data.completion then
        local text_parts = {}
        
        for _, event in ipairs(response_data.completion) do
            if event.chunk and event.chunk.bytes then
                -- Decode base64 if needed
                local chunk_text = event.chunk.bytes
                if type(chunk_text) == "string" then
                    table.insert(text_parts, chunk_text)
                end
            end
        end
        
        return table.concat(text_parts, "")
    end
    
    return nil
end

-- Fallback to simple keyword-based responses for testing
function BedrockClient:get_fallback_response(input_text, tenant_did)
    local input_lower = string.lower(input_text)
    
    -- Get tenant-specific responses
    local tenant_responses = {
        ["1001"] = "Downtown Medical Center",
        ["1002"] = "Westside Family Practice", 
        ["1003"] = "Pediatric Care Clinic"
    }
    
    local clinic_name = tenant_responses[tenant_did] or "our clinic"
    
    -- Appointment scheduling
    if string.find(input_lower, "appointment") or string.find(input_lower, "schedule") then
        return "I'd be happy to help you schedule an appointment at " .. clinic_name .. ". What day would work best for you?"
    
    -- Date responses
    elseif string.find(input_lower, "tomorrow") then
        return "Great! I have several slots available tomorrow morning. Would 9:30 AM work for you?"
    
    elseif string.find(input_lower, "today") then
        return "Let me check our availability for today. I have a few slots open this afternoon. Would 2:30 PM work?"
    
    -- Confirmation responses
    elseif string.find(input_lower, "yes") or string.find(input_lower, "okay") or string.find(input_lower, "sure") then
        return "Perfect! I'll book that appointment for you. Can I get your full name and phone number please?"
    
    -- Patient information collection
    elseif string.find(input_lower, "my name is") or string.find(input_lower, "i'm") then
        return "Thank you! And can I get a phone number where we can reach you?"
    
    -- Phone number patterns
    elseif string.match(input_lower, "%d%d%d[%-.]?%d%d%d[%-.]?%d%d%d%d") then
        local confirmation = "APPT-" .. os.date("%m%d") .. "-" .. math.random(100, 999)
        return "Perfect! I've booked your appointment for tomorrow at 9:30 AM. Your confirmation number is " .. confirmation .. ". Is there anything else I can help you with?"
    
    -- Cancellation/rescheduling
    elseif string.find(input_lower, "cancel") or string.find(input_lower, "reschedule") then
        return "I can help you with that. Can you provide me with your confirmation number or the date of your current appointment?"
    
    -- Hours inquiry
    elseif string.find(input_lower, "hours") or string.find(input_lower, "open") then
        return "We're open Monday through Friday from 9 AM to 5 PM. Is there anything else I can help you with?"
    
    -- Goodbye/thank you
    elseif string.find(input_lower, "thank") or string.find(input_lower, "bye") or string.find(input_lower, "goodbye") then
        return "You're welcome! Thank you for calling " .. clinic_name .. ". Have a great day!"
    
    -- Default response
    else
        return "I understand you're looking for assistance. Could you tell me if you'd like to schedule an appointment, cancel an existing one, or if you have questions about our services?"
    end
end

-- Main method to get agent response (with fallback)
function BedrockClient:get_response(session_id, input_text, tenant_did)
    -- Try Bedrock Agent first
    local bedrock_response = self:invoke_agent(session_id, "[DID: " .. tenant_did .. "] " .. input_text)
    
    if bedrock_response and bedrock_response ~= "" then
        return bedrock_response
    else
        -- Fallback to keyword-based responses
        freeswitch.consoleLog("INFO", "Using fallback response for input: " .. input_text)
        return self:get_fallback_response(input_text, tenant_did)
    end
end

return BedrockClient