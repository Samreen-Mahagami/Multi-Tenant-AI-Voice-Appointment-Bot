package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

type CallSession struct {
	CallID   string
	DID      string
	WS       *websocket.Conn
	WriteMu  sync.Mutex
	Greeting string
	Voice    string
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Println("Starting Simple Media Gateway for FreeSWITCH...")

	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/ws/audio", handleAudioWS)

	log.Println("Media Gateway listening on :8080")
	log.Println("Ready for FreeSWITCH connections")
	
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"healthy","service":"simple-media-gateway"}`))
}

func handleAudioWS(w http.ResponseWriter, r *http.Request) {
	// Extract call info from FreeSWITCH
	callID := r.Header.Get("X-Call-ID")
	if callID == "" {
		callID = "test-call-" + time.Now().Format("150405")
	}
	
	did := r.Header.Get("X-DID")
	if did == "" {
		did = r.URL.Query().Get("did")
	}
	if did == "" {
		did = "1001" // Default
	}

	log.Printf("New call: ID=%s, DID=%s", callID, did)

	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}
	defer ws.Close()

	// Get tenant info
	tenant := getTenantInfo(did)
	
	session := &CallSession{
		CallID:   callID,
		DID:      did,
		WS:       ws,
		Greeting: tenant.Greeting,
		Voice:    tenant.Voice,
	}

	// Send greeting
	go func() {
		time.Sleep(500 * time.Millisecond)
		session.sendGreeting()
	}()

	// Handle incoming audio (simplified)
	for {
		ws.SetReadDeadline(time.Now().Add(30 * time.Second))
		_, data, err := ws.ReadMessage()
		if err != nil {
			log.Printf("WebSocket read error: %v", err)
			break
		}

		// For demo: just log that we received audio
		if len(data) > 0 {
			log.Printf("[%s] Received %d bytes of audio", callID, len(data))
			
			// Simulate processing after 2 seconds of audio
			go func() {
				time.Sleep(2 * time.Second)
				session.sendResponse("I heard you! I'm a simple AI assistant. How can I help you book an appointment?")
			}()
		}
	}
}

func (s *CallSession) sendGreeting() {
	log.Printf("[%s] Sending greeting: %s", s.CallID, s.Greeting)
	s.sendResponse(s.Greeting)
}

func (s *CallSession) sendResponse(text string) {
	log.Printf("[%s] Speaking: %s", s.CallID, text)
	
	// For demo: send simple audio response (silence with metadata)
	s.WriteMu.Lock()
	defer s.WriteMu.Unlock()
	
	// Send some dummy audio data to keep the connection alive
	dummyAudio := make([]byte, 1600) // 100ms of silence at 8kHz 16-bit
	for i := 0; i < 30; i++ { // 3 seconds of audio
		if err := s.WS.WriteMessage(websocket.BinaryMessage, dummyAudio); err != nil {
			log.Printf("[%s] Write error: %v", s.CallID, err)
			break
		}
		time.Sleep(100 * time.Millisecond)
	}
}

type TenantInfo struct {
	Name     string `json:"name"`
	Greeting string `json:"greeting"`
	Voice    string `json:"voice"`
}

func getTenantInfo(did string) TenantInfo {
	// Try to get from tenant service
	if tenant := fetchTenantFromService(did); tenant != nil {
		return *tenant
	}
	
	// Fallback to hardcoded
	switch did {
	case "1001":
		return TenantInfo{
			Name:     "Downtown Medical Center",
			Greeting: "Hello! Thank you for calling Downtown Medical Center. How can I help you today?",
			Voice:    "Joanna",
		}
	case "1002":
		return TenantInfo{
			Name:     "Westside Family Practice",
			Greeting: "Hi there! You've reached Westside Family Practice. How may I assist you today?",
			Voice:    "Matthew",
		}
	case "1003":
		return TenantInfo{
			Name:     "Pediatric Care Clinic",
			Greeting: "Welcome to Pediatric Care Clinic! We're here to help with your child's health needs.",
			Voice:    "Salli",
		}
	default:
		return TenantInfo{
			Name:     "Medical Clinic",
			Greeting: "Hello! How can I help you today?",
			Voice:    "Joanna",
		}
	}
}

func fetchTenantFromService(did string) *TenantInfo {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	url := fmt.Sprintf("http://tenant-config-go:7001/v1/tenants/resolve?did=%s", did)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil
	}
	
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Failed to fetch tenant: %v", err)
		return nil
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != 200 {
		return nil
	}
	
	var result struct {
		DisplayName string `json:"display_name"`
		Greeting    string `json:"greeting"`
		PollyVoiceId string `json:"polly_voice_id"`
	}
	
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil
	}
	
	return &TenantInfo{
		Name:     result.DisplayName,
		Greeting: result.Greeting,
		Voice:    result.PollyVoiceId,
	}
}