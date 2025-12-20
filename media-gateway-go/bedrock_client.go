package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/bedrockagentruntime"
	"github.com/aws/aws-sdk-go-v2/service/bedrockagentruntime/types"
)

var (
	bedrockClient   *bedrockagentruntime.Client
	bedrockAgentId  string
	bedrockAliasId  string
)

func initBedrockClient(ctx context.Context) error {
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return fmt.Errorf("failed to load AWS config: %w", err)
	}

	bedrockClient = bedrockagentruntime.NewFromConfig(cfg)
	bedrockAgentId = os.Getenv("BEDROCK_AGENT_ID")
	bedrockAliasId = os.Getenv("BEDROCK_AGENT_ALIAS_ID")

	if bedrockAgentId == "" || bedrockAliasId == "" {
		return fmt.Errorf("BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set")
	}

	log.Printf("Bedrock client initialized: agentId=%s, aliasId=%s", bedrockAgentId, bedrockAliasId)
	return nil
}

// BedrockAgentResponse represents the response from invoking the agent
type BedrockAgentResponse struct {
	Completion      string `json:"completion"`
	SessionId       string `json:"sessionId"`
	RequiresHandoff bool   `json:"requiresHandoff"`
	HandoffReason   string `json:"handoffReason,omitempty"`
}

// InvokeBedrockAgent calls the Bedrock Agent and returns the response
func InvokeBedrockAgent(ctx context.Context, sessionId, inputText string, sessionAttrs map[string]string) (*BedrockAgentResponse, error) {
	if bedrockClient == nil {
		return nil, fmt.Errorf("bedrock client not initialized")
	}

	log.Printf("[%s] Invoking Bedrock Agent with input: %s", sessionId, inputText)

	input := &bedrockagentruntime.InvokeAgentInput{
		AgentId:      aws.String(bedrockAgentId),
		AgentAliasId: aws.String(bedrockAliasId),
		SessionId:    aws.String(sessionId),
		InputText:    aws.String(inputText),
	}

	// Add session attributes if provided
	if len(sessionAttrs) > 0 {
		input.SessionState = &types.SessionState{
			SessionAttributes: sessionAttrs,
		}
	}

	output, err := bedrockClient.InvokeAgent(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to invoke agent: %w", err)
	}

	// Process the streaming response
	response := &BedrockAgentResponse{
		SessionId: sessionId,
	}

	var completionBuilder strings.Builder

	// Read from the event stream
	stream := output.GetStream()
	defer stream.Close()

	for event := range stream.Events() {
		switch v := event.(type) {
		case *types.ResponseStreamMemberChunk:
			// Append text chunks to build the full response
			if v.Value.Bytes != nil {
				completionBuilder.Write(v.Value.Bytes)
			}

		case *types.ResponseStreamMemberTrace:
			// Log trace information for debugging
			if v.Value.Trace != nil {
				logAgentTrace(sessionId, &v.Value.Trace)
			}

		case *types.ResponseStreamMemberReturnControl:
			// Agent wants to return control (e.g., for handoff)
			log.Printf("[%s] Agent returning control", sessionId)
			response.RequiresHandoff = true
			response.HandoffReason = "Agent requested control return"
		}
	}

	// Check for stream errors
	if err := stream.Err(); err != nil {
		return nil, fmt.Errorf("stream error: %w", err)
	}

	response.Completion = strings.TrimSpace(completionBuilder.String())

	// Check if the response indicates a handoff
	if containsHandoffSignal(response.Completion) {
		response.RequiresHandoff = true
		response.HandoffReason = "Agent initiated handoff"
	}

	log.Printf("[%s] Agent response: %s", sessionId, response.Completion)

	return response, nil
}

func logAgentTrace(sessionId string, trace *types.Trace) {
	// Simple trace logging - the Trace interface may vary by SDK version
	log.Printf("[%s] Trace - Agent processing step", sessionId)
}

func containsHandoffSignal(text string) bool {
	handoffPhrases := []string{
		"connect you with a human",
		"transfer you to",
		"human receptionist",
		"TRANSFER_TO_HUMAN",
		"HANDOFF_INITIATED",
	}

	lowerText := strings.ToLower(text)
	for _, phrase := range handoffPhrases {
		if strings.Contains(lowerText, strings.ToLower(phrase)) {
			return true
		}
	}
	return false
}

// EndBedrockSession explicitly ends a session (optional - sessions auto-expire)
func EndBedrockSession(sessionId string) {
	log.Printf("[%s] Session ended", sessionId)
	// Bedrock Agent sessions auto-expire based on IdleSessionTTL
	// No explicit end session API call needed
}