package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"log"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

var s3Client *s3.Client

// InitS3Client initializes the S3 client
func InitS3Client(cfg aws.Config) {
	s3Client = s3.NewFromConfig(cfg)
	log.Println("✅ S3 client initialized for audio storage")
}

// StoreAudioToS3 stores audio data to S3 and returns the S3 URI
func StoreAudioToS3(ctx context.Context, bucket, callID string, audioData []byte, format string) (string, error) {
	if s3Client == nil {
		return "", fmt.Errorf("S3 client not initialized")
	}

	// Generate unique key for audio file
	timestamp := time.Now().Format("20060102-150405")
	key := fmt.Sprintf("audio/input/%s/%s.%s", callID, timestamp, format)

	log.Printf("[%s] 📦 Storing audio to S3: s3://%s/%s (%d bytes)", callID, bucket, key, len(audioData))

	// Upload to S3
	_, err := s3Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader(audioData),
		ContentType: aws.String(fmt.Sprintf("audio/%s", format)),
		Metadata: map[string]string{
			"call-id":   callID,
			"timestamp": timestamp,
			"type":      "voice-input",
		},
	})

	if err != nil {
		return "", fmt.Errorf("failed to upload audio to S3: %w", err)
	}

	s3URI := fmt.Sprintf("s3://%s/%s", bucket, key)
	log.Printf("[%s] ✅ Audio stored successfully: %s", callID, s3URI)

	return s3URI, nil
}

// StorePollyAudioToS3 stores Polly-generated audio to S3
func StorePollyAudioToS3(ctx context.Context, bucket, callID string, audioStream io.Reader) (string, error) {
	if s3Client == nil {
		return "", fmt.Errorf("S3 client not initialized")
	}

	// Generate unique key for Polly audio
	timestamp := time.Now().Format("20060102-150405")
	key := fmt.Sprintf("audio/output/%s/%s.mp3", callID, timestamp)

	log.Printf("[%s] 📦 Storing Polly audio to S3: s3://%s/%s", callID, bucket, key)

	// Read audio stream into buffer
	audioData, err := io.ReadAll(audioStream)
	if err != nil {
		return "", fmt.Errorf("failed to read audio stream: %w", err)
	}

	// Upload to S3
	_, err = s3Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader(audioData),
		ContentType: aws.String("audio/mpeg"),
		Metadata: map[string]string{
			"call-id":   callID,
			"timestamp": timestamp,
			"type":      "voice-output",
			"source":    "polly",
		},
	})

	if err != nil {
		return "", fmt.Errorf("failed to upload Polly audio to S3: %w", err)
	}

	s3URI := fmt.Sprintf("s3://%s/%s", bucket, key)
	log.Printf("[%s] ✅ Polly audio stored successfully: %s", callID, s3URI)

	return s3URI, nil
}

// GetAudioFromS3 retrieves audio from S3
func GetAudioFromS3(ctx context.Context, bucket, key string) ([]byte, error) {
	if s3Client == nil {
		return nil, fmt.Errorf("S3 client not initialized")
	}

	log.Printf("📥 Retrieving audio from S3: s3://%s/%s", bucket, key)

	result, err := s3Client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})

	if err != nil {
		return nil, fmt.Errorf("failed to get audio from S3: %w", err)
	}
	defer result.Body.Close()

	audioData, err := io.ReadAll(result.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read audio data: %w", err)
	}

	log.Printf("✅ Retrieved %d bytes from S3", len(audioData))
	return audioData, nil
}

// GeneratePresignedURL generates a presigned URL for audio playback
func GeneratePresignedURL(ctx context.Context, bucket, key string, duration time.Duration) (string, error) {
	if s3Client == nil {
		return "", fmt.Errorf("S3 client not initialized")
	}

	presignClient := s3.NewPresignClient(s3Client)

	request, err := presignClient.PresignGetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	}, func(opts *s3.PresignOptions) {
		opts.Expires = duration
	})

	if err != nil {
		return "", fmt.Errorf("failed to generate presigned URL: %w", err)
	}

	log.Printf("🔗 Generated presigned URL (expires in %v)", duration)
	return request.URL, nil
}

// StoreConversationLog stores conversation transcript to S3 for analytics
func StoreConversationLog(ctx context.Context, bucket, callID string, transcript string) error {
	if s3Client == nil {
		return fmt.Errorf("S3 client not initialized")
	}

	timestamp := time.Now().Format("20060102-150405")
	key := fmt.Sprintf("transcripts/%s/%s.txt", callID, timestamp)

	log.Printf("[%s] 📝 Storing conversation transcript to S3", callID)

	_, err := s3Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader([]byte(transcript)),
		ContentType: aws.String("text/plain"),
		Metadata: map[string]string{
			"call-id":   callID,
			"timestamp": timestamp,
			"type":      "transcript",
		},
	})

	if err != nil {
		return fmt.Errorf("failed to store transcript: %w", err)
	}

	log.Printf("[%s] ✅ Transcript stored: s3://%s/%s", callID, bucket, key)
	return nil
}
