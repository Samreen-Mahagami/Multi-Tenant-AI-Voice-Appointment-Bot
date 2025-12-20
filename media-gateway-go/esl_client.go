package main

import (
	"fmt"
	"log"
	"net"
	"strings"
	"time"
)

// ESLUuidBreak sends a break command to FreeSWITCH to interrupt audio playback
func ESLUuidBreak(callId string, config ESLConfig) error {
	log.Printf("🚫 Sending break command to FreeSWITCH for call: %s", callId)

	// Connect to FreeSWITCH Event Socket
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%s", config.Host, config.Port), 5*time.Second)
	if err != nil {
		return fmt.Errorf("failed to connect to FreeSWITCH ESL: %w", err)
	}
	defer conn.Close()

	// Authenticate
	authCmd := fmt.Sprintf("auth %s\n\n", config.Password)
	if _, err := conn.Write([]byte(authCmd)); err != nil {
		return fmt.Errorf("failed to authenticate: %w", err)
	}

	// Read auth response
	buffer := make([]byte, 1024)
	if _, err := conn.Read(buffer); err != nil {
		return fmt.Errorf("failed to read auth response: %w", err)
	}

	// Send break command
	breakCmd := fmt.Sprintf("api uuid_break %s all\n\n", callId)
	if _, err := conn.Write([]byte(breakCmd)); err != nil {
		return fmt.Errorf("failed to send break command: %w", err)
	}

	// Read response
	if _, err := conn.Read(buffer); err != nil {
		return fmt.Errorf("failed to read break response: %w", err)
	}

	response := string(buffer)
	if strings.Contains(response, "+OK") {
		log.Printf("✅ Break command sent successfully for call: %s", callId)
		return nil
	}

	return fmt.Errorf("break command failed: %s", response)
}

// ESLGetChannelInfo gets information about a channel
func ESLGetChannelInfo(callId string, config ESLConfig) (map[string]string, error) {
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%s", config.Host, config.Port), 5*time.Second)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to FreeSWITCH ESL: %w", err)
	}
	defer conn.Close()

	// Authenticate
	authCmd := fmt.Sprintf("auth %s\n\n", config.Password)
	if _, err := conn.Write([]byte(authCmd)); err != nil {
		return nil, fmt.Errorf("failed to authenticate: %w", err)
	}

	// Read auth response
	buffer := make([]byte, 1024)
	if _, err := conn.Read(buffer); err != nil {
		return nil, fmt.Errorf("failed to read auth response: %w", err)
	}

	// Send channel info command
	infoCmd := fmt.Sprintf("api uuid_dump %s\n\n", callId)
	if _, err := conn.Write([]byte(infoCmd)); err != nil {
		return nil, fmt.Errorf("failed to send info command: %w", err)
	}

	// Read response
	responseBuffer := make([]byte, 4096)
	n, err := conn.Read(responseBuffer)
	if err != nil {
		return nil, fmt.Errorf("failed to read info response: %w", err)
	}

	response := string(responseBuffer[:n])
	
	// Parse the response into key-value pairs
	info := make(map[string]string)
	lines := strings.Split(response, "\n")
	
	for _, line := range lines {
		if strings.Contains(line, ": ") {
			parts := strings.SplitN(line, ": ", 2)
			if len(parts) == 2 {
				info[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
			}
		}
	}

	return info, nil
}

// ESLHangupCall hangs up a call
func ESLHangupCall(callId string, config ESLConfig) error {
	log.Printf("📞 Hanging up call: %s", callId)

	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%s", config.Host, config.Port), 5*time.Second)
	if err != nil {
		return fmt.Errorf("failed to connect to FreeSWITCH ESL: %w", err)
	}
	defer conn.Close()

	// Authenticate
	authCmd := fmt.Sprintf("auth %s\n\n", config.Password)
	if _, err := conn.Write([]byte(authCmd)); err != nil {
		return fmt.Errorf("failed to authenticate: %w", err)
	}

	// Read auth response
	buffer := make([]byte, 1024)
	if _, err := conn.Read(buffer); err != nil {
		return fmt.Errorf("failed to read auth response: %w", err)
	}

	// Send hangup command
	hangupCmd := fmt.Sprintf("api uuid_kill %s\n\n", callId)
	if _, err := conn.Write([]byte(hangupCmd)); err != nil {
		return fmt.Errorf("failed to send hangup command: %w", err)
	}

	// Read response
	if _, err := conn.Read(buffer); err != nil {
		return fmt.Errorf("failed to read hangup response: %w", err)
	}

	log.Printf("✅ Call hangup command sent for: %s", callId)
	return nil
}