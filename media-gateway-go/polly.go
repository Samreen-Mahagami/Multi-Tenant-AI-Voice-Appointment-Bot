package main

import (
	"context"
	"fmt"
	"io"
	"log"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/polly"
	"github.com/aws/aws-sdk-go-v2/service/polly/types"
)

// PollyPCMStream generates PCM audio stream from text using Amazon Polly
func PollyPCMStream(ctx context.Context, client *polly.Client, voiceId, engine, text string) (io.ReadCloser, error) {
	log.Printf("🔊 Generating REAL Polly TTS: voice=%s, engine=%s, text=\"%s\"", voiceId, engine, text)

	// Prepare the synthesis input
	input := &polly.SynthesizeSpeechInput{
		Text:         aws.String(text),
		VoiceId:      types.VoiceId(voiceId),
		OutputFormat: types.OutputFormatPcm,
		SampleRate:   aws.String("8000"), // Match FreeSWITCH sample rate
		TextType:     types.TextTypeText,
	}

	// Set engine if specified
	if engine == "neural" {
		input.Engine = types.EngineNeural
	} else {
		input.Engine = types.EngineStandard
	}

	// Call Polly
	output, err := client.SynthesizeSpeech(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to synthesize speech: %w", err)
	}

	log.Printf("✅ Polly TTS generated successfully")
	return output.AudioStream, nil
}

// GetAvailableVoices returns list of available Polly voices
func GetAvailableVoices(ctx context.Context, client *polly.Client) ([]types.Voice, error) {
	input := &polly.DescribeVoicesInput{
		LanguageCode: types.LanguageCodeEnUs,
	}

	output, err := client.DescribeVoices(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to describe voices: %w", err)
	}

	return output.Voices, nil
}

// ValidateVoice checks if a voice ID is valid
func ValidateVoice(ctx context.Context, client *polly.Client, voiceId string) bool {
	voices, err := GetAvailableVoices(ctx, client)
	if err != nil {
		log.Printf("❌ Failed to validate voice: %v", err)
		return false
	}

	for _, voice := range voices {
		if string(voice.Id) == voiceId {
			return true
		}
	}

	return false
}

// OptimizeTextForSpeech prepares text for better TTS output
func OptimizeTextForSpeech(text string) string {
	// Add SSML tags for better pronunciation if needed
	// For now, just return the text as-is
	return text
}