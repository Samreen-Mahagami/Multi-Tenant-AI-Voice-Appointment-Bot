package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  16384,
	WriteBufferSize: 16384,
}

// TenantInfo holds tenant configuration
type TenantInfo struct {
	TenantId     string `json:"tenantId"`
	DisplayName  string `json:"displayName"`
	PollyVoiceId string `json:"pollyVoiceId"`
	PollyEngine  string `json:"pollyEngine"`
	Greeting     string `json:"greeting"`
}

// CallSession represents an active call
type CallSession struct {
	CallID      string
	DID         string
	Tenant      *TenantInfo
	Ctx         context.Context
	Cancel      context.CancelFunc
	WS          *websocket.Conn
	BotSpeaking atomic.Bool
	AudioCh     chan []byte
	WriteMu     sync.Mutex
}

func HandleAudioWS(w http.ResponseWriter, r *http.Request) {
	callID := r.URL.Query().Get("callId")
	did := r.URL.Query().Get("did")

	if callID == "" || did == "" {
		log.Printf("Missing callId or did in request")
		http.Error(w, "missing callId or did", http.StatusBadRequest)
		return
	}

	log.Printf("🎙️ New REAL VOICE WebSocket connection: callId=%s, did=%s", callID, did)

	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}

	ctx, cancel := context.WithCancel(context.Background())

	// Resolve tenant from DID
	tenant, err := resolveTenant(ctx, did)
	if err != nil {
		log.Printf("Failed to resolve tenant for DID %s: %v", did, err)
		tenant = &TenantInfo{
			TenantId:     "default",
			DisplayName:  "Medical Clinic",
			PollyVoiceId: "Joanna",
			PollyEngine:  "neural",
			Greeting:     "Hello! How can I help you today?",
		}
	}

	session := &CallSession{
		CallID:  callID,
		DID:     did,
		Tenant:  tenant,
		Ctx:     ctx,
		Cancel:  cancel,
		WS:      ws,
		AudioCh: make(chan []byte, 128),
	}

	defer func() {
		cancel()
		close(session.AudioCh)
		ws.Close()
		EndBedrockSession(callID)
		log.Printf("📞 Real voice call ended: %s", callID)
	}()

	// Start Transcribe streaming in background
	go session.startTranscribeStream()

	// Send initial greeting
	go func() {
		time.Sleep(500 * time.Millisecond)
		session.processInitialGreeting()
	}()

	// Read audio frames from FreeSWITCH or browser
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		// Set longer timeout for browser mode since browser doesn't send continuous audio
		timeout := 30 * time.Second
		if transcribeClient == nil { // Browser mode
			timeout = 5 * time.Minute // Much longer timeout for browser mode
		}
		
		ws.SetReadDeadline(time.Now().Add(timeout))
		mt, data, err := ws.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("WebSocket read error: %v", err)
			}
			return
		}

		if mt == websocket.TextMessage {
			// Handle text messages from browser (browser mode)
			var msg map[string]interface{}
			if err := json.Unmarshal(data, &msg); err == nil {
				if msgType, ok := msg["type"].(string); ok {
					switch msgType {
					case "transcript":
						if text, ok := msg["text"].(string); ok && text != "" {
							log.Printf("[%s] 📝 Browser transcript: %s", callID, text)
							session.processAgentTurn(text)
						}
					case "heartbeat":
						// Keep connection alive
						log.Printf("[%s] 💓 Heartbeat received", callID)
					}
				}
			}
			continue
		}

		if mt != websocket.BinaryMessage {
			continue
		}

		// Real audio data from FreeSWITCH (only in real AWS mode)
		if transcribeClient != nil {
			select {
			case session.AudioCh <- data:
			default:
			}
		}
	}
}

func (s *CallSession) startTranscribeStream() {
	// Check if we have real AWS Transcribe client
	if transcribeClient == nil {
		log.Printf("[%s] 🎭 Browser Mode: Using browser speech recognition instead of AWS Transcribe", s.CallID)
		return
	}

	err := StartTranscribe(
		s.Ctx,
		transcribeClient,
		s.AudioCh,
		func(text string) {
			log.Printf("[%s] 📝 REAL Transcribe result: %s", s.CallID, text)
			if text != "" {
				s.processAgentTurn(text)
			}
		},
		func() {
			if s.BotSpeaking.Load() {
				log.Printf("[%s] 🚫 Barge-in detected - stopping AI speech", s.CallID)
				s.BotSpeaking.Store(false)
				ESLUuidBreak(s.CallID, eslConfig)
			}
		},
	)

	if err != nil {
		log.Printf("[%s] ❌ Transcribe error: %v", s.CallID, err)
	}
}

func (s *CallSession) processInitialGreeting() {
	// Send greeting immediately for better user experience
	greeting := s.Tenant.Greeting
	log.Printf("[%s] 🎤 Sending initial greeting: %s", s.CallID, greeting)
	
	// Send greeting via browser TTS for now (to ensure it works)
	response := map[string]interface{}{
		"type":   "greeting",
		"text":   greeting,
		"voice":  s.Tenant.PollyVoiceId,
		"engine": s.Tenant.PollyEngine,
	}
	
	s.WriteMu.Lock()
	writeErr := s.WS.WriteJSON(response)
	s.WriteMu.Unlock()
	
	if writeErr != nil {
		log.Printf("[%s] ❌ WebSocket write error: %v", s.CallID, writeErr)
	} else {
		log.Printf("[%s] ✅ Greeting sent to browser", s.CallID)
	}
}

func (s *CallSession) processAgentTurn(userText string) {
	// Store conversation transcript to S3
	if s3Client != nil {
		go func() {
			transcript := fmt.Sprintf("[%s] User: %s\n", time.Now().Format("15:04:05"), userText)
			StoreConversationLog(s.Ctx, s3Bucket, s.CallID, transcript)
		}()
	}

	// Check if we have real Bedrock client
	if bedrockClient == nil {
		log.Printf("[%s] 🎭 Browser Mode: Simulating AI response for: \"%s\"", s.CallID, userText)
		
		// Simple fallback responses
		var response string
		lowerText := strings.ToLower(userText)
		
		if strings.Contains(lowerText, "appointment") || strings.Contains(lowerText, "book") {
			response = "I'd be happy to help you book an appointment. What day works best for you?"
		} else if strings.Contains(lowerText, "tomorrow") || strings.Contains(lowerText, "morning") {
			response = "Let me check our availability for tomorrow morning. I have slots at 9 AM, 9:30 AM, and 10 AM. Which would you prefer?"
		} else if strings.Contains(lowerText, "9:30") || strings.Contains(lowerText, "930") {
			response = "Perfect! I can book you for 9:30 AM tomorrow. May I have your full name please?"
		} else if strings.Contains(lowerText, "name") || len(strings.Fields(userText)) >= 2 {
			response = "Thank you! And what's the best email address to send your confirmation?"
		} else if strings.Contains(lowerText, "@") || strings.Contains(lowerText, "email") {
			response = "Perfect! I've booked your appointment for tomorrow at 9:30 AM. Your confirmation number is APPT-1220-001. You'll receive an email confirmation shortly. Is there anything else I can help you with?"
		} else {
			response = "I understand. How can I help you today?"
		}
		
		s.speakResponse(response)
		return
	}

	sessionAttrs := map[string]string{
		"tenant_id":   s.Tenant.TenantId,
		"tenant_name": s.Tenant.DisplayName,
	}

	log.Printf("[%s] 🧠 Sending to REAL Bedrock Agent: \"%s\"", s.CallID, userText)

	resp, err := InvokeBedrockAgent(s.Ctx, s.CallID, userText, sessionAttrs)
	if err != nil {
		log.Printf("[%s] ❌ Bedrock Agent error: %v", s.CallID, err)
		s.speakResponse("I'm sorry, I'm having trouble right now. Could you please repeat that?")
		return
	}

	if resp.Completion != "" {
		log.Printf("[%s] ✅ Bedrock Agent response: \"%s\"", s.CallID, resp.Completion)
		
		// Store AI response to S3
		if s3Client != nil {
			go func() {
				transcript := fmt.Sprintf("[%s] AI: %s\n", time.Now().Format("15:04:05"), resp.Completion)
				StoreConversationLog(s.Ctx, s3Bucket, s.CallID, transcript)
			}()
		}
		
		s.speakResponse(resp.Completion)
	}

	if resp.RequiresHandoff {
		log.Printf("[%s] 🔄 Handoff required: %s", s.CallID, resp.HandoffReason)
		// In production, would initiate actual call transfer here
		time.Sleep(2 * time.Second)
		s.Cancel()
	}

	// Check for end-of-call signals
	if containsEndCallSignal(resp.Completion) {
		log.Printf("[%s] 👋 End of call detected", s.CallID)
		time.Sleep(3 * time.Second) // Let final speech play
		s.Cancel()
	}
}

func (s *CallSession) speakResponse(text string) {
	s.BotSpeaking.Store(true)
	defer s.BotSpeaking.Store(false)

	// Check if we have real Polly client
	if pollyClient == nil {
		log.Printf("[%s] 🎭 Browser Mode: Sending text for browser TTS: \"%s\"", s.CallID, text)
		
		// Send response to browser for TTS
		response := map[string]interface{}{
			"type":   "response",
			"text":   text,
			"voice":  s.Tenant.PollyVoiceId,
			"engine": s.Tenant.PollyEngine,
		}
		
		s.WriteMu.Lock()
		writeErr := s.WS.WriteJSON(response)
		s.WriteMu.Unlock()
		
		if writeErr != nil {
			log.Printf("[%s] ❌ WebSocket write error: %v", s.CallID, writeErr)
		}
		
		// Simulate speaking duration
		words := len(strings.Fields(text))
		duration := time.Duration(words*300) * time.Millisecond // ~300ms per word
		if duration < 2*time.Second {
			duration = 2 * time.Second
		}
		
		time.Sleep(duration)
		log.Printf("[%s] ✅ Browser voice response completed", s.CallID)
		return
	}

	log.Printf("[%s] 🔊 REAL Polly TTS: \"%s\" (Voice: %s)", s.CallID, text, s.Tenant.PollyVoiceId)

	// Optimize text for speech
	optimizedText := optimizeForSpeech(text)

	audioStream, err := PollyPCMStream(s.Ctx, pollyClient, s.Tenant.PollyVoiceId, s.Tenant.PollyEngine, optimizedText)
	if err != nil {
		log.Printf("[%s] ❌ Polly error: %v", s.CallID, err)
		log.Printf("[%s] 🎭 Falling back to browser TTS due to Polly error", s.CallID)
		
		// Fall back to browser TTS
		response := map[string]interface{}{
			"type":   "response",
			"text":   text,
			"voice":  s.Tenant.PollyVoiceId,
			"engine": s.Tenant.PollyEngine,
		}
		
		s.WriteMu.Lock()
		writeErr := s.WS.WriteJSON(response)
		s.WriteMu.Unlock()
		
		if writeErr != nil {
			log.Printf("[%s] ❌ WebSocket write error: %v", s.CallID, writeErr)
		}
		return
	}
	defer audioStream.Close()

	buf := make([]byte, 3200) // ~200ms at 8kHz 16-bit mono
	for {
		if !s.BotSpeaking.Load() {
			log.Printf("[%s] 🚫 Playback interrupted", s.CallID)
			break
		}

		n, err := audioStream.Read(buf)
		if n > 0 {
			s.WriteMu.Lock()
			writeErr := s.WS.WriteMessage(websocket.BinaryMessage, buf[:n])
			s.WriteMu.Unlock()

			if writeErr != nil {
				log.Printf("[%s] ❌ WebSocket write error: %v", s.CallID, writeErr)
				break
			}
		}

		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("[%s] ❌ Audio read error: %v", s.CallID, err)
			break
		}

		time.Sleep(20 * time.Millisecond)
	}

	log.Printf("[%s] ✅ Real voice response completed", s.CallID)
}

func resolveTenant(ctx context.Context, did string) (*TenantInfo, error) {
	url := tenantConfigURL + "/v1/tenants/resolve?did=" + did

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("tenant not found: status %d", resp.StatusCode)
	}

	var result struct {
		TenantName   string `json:"tenant_name"`
		DisplayName  string `json:"display_name"`
		Greeting     string `json:"greeting"`
		PollyVoiceId string `json:"polly_voice_id"`
		PollyEngine  string `json:"polly_engine"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &TenantInfo{
		TenantId:     result.TenantName,  // Use actual tenant name instead of DID
		DisplayName:  result.DisplayName,
		PollyVoiceId: result.PollyVoiceId,
		PollyEngine:  result.PollyEngine,
		Greeting:     result.Greeting,
	}, nil
}

func containsEndCallSignal(text string) bool {
	endPhrases := []string{
		"have a great day",
		"goodbye",
		"take care",
		"thank you for calling",
	}

	lowerText := strings.ToLower(text)
	for _, phrase := range endPhrases {
		if strings.Contains(lowerText, phrase) {
			return true
		}
	}
	return false
}

func optimizeForSpeech(text string) string {
	// Remove any markdown or formatting
	text = strings.ReplaceAll(text, "**", "")
	text = strings.ReplaceAll(text, "*", "")
	text = strings.ReplaceAll(text, "#", "")
	
	// Convert common abbreviations
	text = strings.ReplaceAll(text, "Dr.", "Doctor")
	text = strings.ReplaceAll(text, "Mr.", "Mister")
	text = strings.ReplaceAll(text, "Mrs.", "Missus")
	text = strings.ReplaceAll(text, "Ms.", "Miss")
	
	return strings.TrimSpace(text)
}