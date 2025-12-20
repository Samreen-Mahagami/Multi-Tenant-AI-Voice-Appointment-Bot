package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/polly"
	"github.com/aws/aws-sdk-go-v2/service/transcribestreaming"
)

var (
	transcribeClient *transcribestreaming.Client
	pollyClient      *polly.Client
	eslConfig        ESLConfig
	tenantConfigURL  string
)

type ESLConfig struct {
	Host     string
	Port     string
	Password string
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Println("Starting Media Gateway with REAL AWS Voice Integration...")

	ctx := context.Background()

	// Load AWS config
	awsCfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Fatalf("Failed to load AWS config: %v", err)
	}

	// Initialize AWS clients
	transcribeClient = transcribestreaming.NewFromConfig(awsCfg)
	pollyClient = polly.NewFromConfig(awsCfg)

	// Initialize Bedrock client
	if err := initBedrockClient(ctx); err != nil {
		log.Fatalf("Failed to initialize Bedrock client: %v", err)
	}

	// Load configuration from environment
	eslConfig = ESLConfig{
		Host:     getEnv("FREESWITCH_ESL_HOST", "freeswitch"),
		Port:     getEnv("FREESWITCH_ESL_PORT", "8021"),
		Password: getEnv("FREESWITCH_ESL_PASSWORD", "ClueCon"),
	}

	tenantConfigURL = getEnv("TENANT_CONFIG_URL", "http://tenant-config-go:7001")

	// Setup HTTP server
	mux := http.NewServeMux()
	mux.HandleFunc("/health", handleHealth)
	mux.HandleFunc("/ws/audio", HandleAudioWS)

	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	// Graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
		<-sigChan

		log.Println("Shutting down...")
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		server.Shutdown(ctx)
	}()

	log.Println("🎙️ Media Gateway listening on :8080")
	log.Printf("🧠 Bedrock Agent ID: %s", bedrockAgentId)
	log.Printf("🎯 Bedrock Agent Alias: %s", bedrockAliasId)
	log.Println("🔊 Real AWS Voice Integration: Transcribe + Polly + Bedrock")

	if err := server.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(fmt.Sprintf(`{
		"status":"healthy",
		"service":"real-voice-media-gateway",
		"agentId":"%s",
		"features":["transcribe","polly","bedrock-agent","freeswitch"]
	}`, bedrockAgentId)))
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}