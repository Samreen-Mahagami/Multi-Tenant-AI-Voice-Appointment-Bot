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
	s3Bucket         string
)

type ESLConfig struct {
	Host     string
	Port     string
	Password string
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	
	ctx := context.Background()

	// Load S3 bucket from environment
	s3Bucket = getEnv("S3_BUCKET", "clinic-voice-processing-089580247707")
	
	// Force AWS mode - try to load AWS config first
	log.Println("🚀 Starting Media Gateway with FULL AWS Voice Integration + S3 Storage...")
	
	// Load AWS config
	awsCfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		log.Printf("❌ Failed to load AWS config: %v", err)
		log.Println("🎭 Falling back to browser mode")
	} else {
		// Initialize AWS clients
		transcribeClient = transcribestreaming.NewFromConfig(awsCfg)
		pollyClient = polly.NewFromConfig(awsCfg)
		
		// Initialize S3 client
		InitS3Client(awsCfg)

		// Initialize Bedrock client
		if err := initBedrockClient(ctx); err != nil {
			log.Printf("❌ Failed to initialize Bedrock client: %v", err)
			log.Println("🎭 Falling back to browser mode")
		} else {
			log.Printf("📦 S3 Bucket configured: %s", s3Bucket)
			log.Println("✅ ALL AWS SERVICES ENABLED")
		}
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
	
	if bedrockAgentId != "" {
		log.Printf("🧠 Bedrock Agent ID: %s", bedrockAgentId)
		log.Printf("🎯 Bedrock Agent Alias: %s", bedrockAliasId)
	}
	
	if transcribeClient != nil && pollyClient != nil && s3Client != nil {
		log.Println("🔊 FULL AWS Voice Integration: S3 → Transcribe → Bedrock → Polly → S3")
		log.Println("🎯 Ready for: Voice → S3 → Transcribe → Bedrock Agent → Polly → S3 → Voice")
	} else {
		log.Println("🎭 Browser Mode: Browser TTS + Simulated AI responses")
	}

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