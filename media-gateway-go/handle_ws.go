package main

import (
	"context"
	"encoding/json"
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

	// Read audio frames from FreeSWITCH
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		ws.SetReadDeadline(time.Now().Add(30 * time.Second))
		mt, data, err := ws.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("WebSocket read error: %v", err)
			}
			return
		}

		if mt != websocket.BinaryMessage {
			continue
		}

		// Real audio data from FreeSWITCH
		select {
		case session.AudioCh <- data:
		default:
		}
	}
}

func (s *CallSession) startTranscribeStream() {
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
	// Create session attributes with tenant context
	sessionAttrs := map[string]string{
		"tenant_id":    s.Tenant.TenantId,
		"tenant_name":  s.Tenant.DisplayName,
		"polly_voice":  s.Tenant.PollyVoiceId,
		"polly_engine": s.Tenant.PollyEngine,
	}

	// First turn: Send empty input to trigger agent's greeting
	resp, err := InvokeBedrockAgent(s.Ctx, s.CallID, "Start conversation", sessionAttrs)
	
	var greeting string
	if err != nil {
		log.Printf("[%s] ❌ Failed to get agent greeting: %v", s.CallID, err)
		greeting = s.Tenant.Greeting
	} else if resp.Completion != "" {
		greeting = resp.Completion
	} else {
		greeting = s.Tenant.Greeting
	}

	s.speakResponse(greeting)
}

func (s *CallSession) processAgentTurn(userText string) {
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

	log.Printf("[%s] 🔊 REAL Polly TTS: \"%s\" (Voice: %s)", s.CallID, text, s.Tenant.PollyVoiceId)

	// Optimize text for speech
	optimizedText := optimizeForSpeech(text)

	audioStream, err := PollyPCMStream(s.Ctx, pollyClient, s.Tenant.PollyVoiceId, s.Tenant.PollyEngine, optimizedText)
	if err != nil {
		log.Printf("[%s] ❌ Polly error: %v", s.CallID, err)
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
		DisplayName  string `json:"display_name"`
		Greeting     string `json:"greeting"`
		PollyVoiceId string `json:"polly_voice_id"`
		PollyEngine  string `json:"polly_engine"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &TenantInfo{
		TenantId:     did,
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