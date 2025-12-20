package main

import (
	"context"
	"encoding/binary"
	"log"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/transcribestreaming"
	"github.com/aws/aws-sdk-go-v2/service/transcribestreaming/types"
)

// StartTranscribe starts a streaming transcription session
func StartTranscribe(
	ctx context.Context,
	client *transcribestreaming.Client,
	audioCh <-chan []byte,
	onTranscript func(string),
	onSpeechStart func(),
) error {
	
	log.Println("🎤 Starting REAL Amazon Transcribe streaming...")

	// Create the streaming input
	input := &transcribestreaming.StartStreamTranscriptionInput{
		LanguageCode:         types.LanguageCodeEnUs,
		MediaEncoding:        types.MediaEncodingPcm,
		MediaSampleRateHertz: aws.Int32(8000), // FreeSWITCH typically uses 8kHz
	}

	// Start the transcription
	output, err := client.StartStreamTranscription(ctx, input)
	if err != nil {
		return err
	}

	// Get the stream for sending audio
	stream := output.GetStream()
	defer stream.Close()

	// Start goroutine to send audio data
	go func() {
		defer stream.Close()
		
		for {
			select {
			case <-ctx.Done():
				return
			case audioData, ok := <-audioCh:
				if !ok {
					return
				}
				
				// Convert audio data to proper format if needed
				processedAudio := processAudioForTranscribe(audioData)
				
				if len(processedAudio) > 0 {
					audioEvent := &types.AudioStreamMemberAudioEvent{
						Value: types.AudioEvent{
							AudioChunk: processedAudio,
						},
					}
					
					if err := stream.Send(ctx, audioEvent); err != nil {
						log.Printf("❌ Error sending audio: %v", err)
						return
					}
				}
			}
		}
	}()

	// Process transcription results
	var speechStarted bool
	var currentTranscript string

	for event := range stream.Events() {
		switch e := event.(type) {
		case *types.TranscriptResultStreamMemberTranscriptEvent:
			result := e.Value.Transcript
			
			if result != nil && len(result.Results) > 0 {
				for _, res := range result.Results {
					if res.Alternatives != nil && len(res.Alternatives) > 0 {
						transcript := aws.ToString(res.Alternatives[0].Transcript)
						
						if transcript != "" {
							if !speechStarted {
								speechStarted = true
								onSpeechStart()
								log.Printf("🎤 Speech detected, starting transcription...")
							}
							
							if !res.IsPartial {
								// Final transcript
								currentTranscript = transcript
								log.Printf("📝 Final transcript: %s", currentTranscript)
								onTranscript(currentTranscript)
								speechStarted = false
								currentTranscript = ""
							} else {
								// Partial transcript
								log.Printf("📝 Partial: %s", transcript)
							}
						}
					}
				}
			}
			
		default:
			log.Printf("❌ Transcribe unknown event type: %T", e)
		}
	}

	if err := stream.Err(); err != nil {
		log.Printf("❌ Transcribe stream error: %v", err)
		return err
	}

	log.Println("✅ Transcribe stream ended")
	return nil
}

// processAudioForTranscribe converts audio data to the format expected by Transcribe
func processAudioForTranscribe(audioData []byte) []byte {
	// FreeSWITCH typically sends 16-bit PCM at 8kHz
	// Transcribe expects the same format, so we might not need conversion
	
	// Basic validation
	if len(audioData) == 0 {
		return nil
	}
	
	// Check if it's silence (optional optimization)
	if isAudioSilence(audioData) {
		return nil // Don't send silence to save bandwidth
	}
	
	// For now, pass through as-is
	// In production, you might want to:
	// - Resample if needed
	// - Apply noise reduction
	// - Normalize volume
	
	return audioData
}

// isAudioSilence detects if audio data is mostly silence
func isAudioSilence(audioData []byte) bool {
	if len(audioData) < 2 {
		return true
	}

	// Simple silence detection - check if most samples are near zero
	var totalAmplitude int64
	sampleCount := len(audioData) / 2

	for i := 0; i < sampleCount; i++ {
		if i*2+1 >= len(audioData) {
			break
		}
		// Convert to 16-bit sample (little endian)
		sample := int16(binary.LittleEndian.Uint16(audioData[i*2:]))
		if sample < 0 {
			totalAmplitude += int64(-sample)
		} else {
			totalAmplitude += int64(sample)
		}
	}

	if sampleCount == 0 {
		return true
	}

	avgAmplitude := totalAmplitude / int64(sampleCount)
	return avgAmplitude < 200 // Silence threshold
}