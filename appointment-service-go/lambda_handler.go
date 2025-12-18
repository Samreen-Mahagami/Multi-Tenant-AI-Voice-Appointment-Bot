package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

// Lambda handler function
func lambdaHandler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	log.Printf("Received request: %s %s", request.HTTPMethod, request.Path)

	// Initialize appointment service if not already done
	if appointmentService == nil {
		appointmentService = NewAppointmentService()
		log.Printf("Appointment service initialized with %d slots", len(appointmentService.slots))
	}

	// Add CORS headers
	headers := map[string]string{
		"Access-Control-Allow-Origin":  "*",
		"Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
		"Access-Control-Allow-Headers": "Content-Type, Authorization",
		"Content-Type":                 "application/json",
	}

	// Handle preflight OPTIONS requests
	if request.HTTPMethod == "OPTIONS" {
		return events.APIGatewayProxyResponse{
			StatusCode: 200,
			Headers:    headers,
			Body:       "",
		}, nil
	}

	// Route the request
	switch {
	case request.Path == "/v1/health" && request.HTTPMethod == "GET":
		return handleHealthLambda(headers)

	case request.Path == "/v1/slots/search" && request.HTTPMethod == "POST":
		return handleSearchSlotsLambda(request, headers)

	case request.Path == "/v1/appointments/confirm" && request.HTTPMethod == "POST":
		return handleConfirmAppointmentLambda(request, headers)

	default:
		return errorResponse(404, "Not found"), nil
	}
}

func handleHealthLambda(headers map[string]string) (events.APIGatewayProxyResponse, error) {
	response := map[string]interface{}{
		"status":       "healthy",
		"service":      "appointment-service",
		"timestamp":    "2025-12-18T10:00:00Z",
		"appointments": len(appointmentService.appointments),
		"slots":        len(appointmentService.slots),
	}

	body, _ := json.Marshal(response)
	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Headers:    headers,
		Body:       string(body),
	}, nil
}

func handleSearchSlotsLambda(request events.APIGatewayProxyRequest, headers map[string]string) (events.APIGatewayProxyResponse, error) {
	var req SearchSlotsRequest
	if err := json.Unmarshal([]byte(request.Body), &req); err != nil {
		return errorResponse(400, "Invalid request body"), nil
	}

	slots, err := appointmentService.SearchSlots(req.TenantID, req.Date, req.TimePreference)
	if err != nil {
		return errorResponse(400, err.Error()), nil
	}

	response := map[string]interface{}{
		"slots": slots,
		"count": len(slots),
	}

	body, _ := json.Marshal(response)
	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Headers:    headers,
		Body:       string(body),
	}, nil
}

func handleConfirmAppointmentLambda(request events.APIGatewayProxyRequest, headers map[string]string) (events.APIGatewayProxyResponse, error) {
	var req ConfirmAppointmentRequest
	if err := json.Unmarshal([]byte(request.Body), &req); err != nil {
		return errorResponse(400, "Invalid request body"), nil
	}

	appointment, err := appointmentService.ConfirmAppointment(req.TenantID, req.SlotID, req.PatientName, req.PatientEmail)
	if err != nil {
		response := map[string]interface{}{
			"status": "FAILED",
			"error":  err.Error(),
		}
		body, _ := json.Marshal(response)
		return events.APIGatewayProxyResponse{
			StatusCode: 400,
			Headers:    headers,
			Body:       string(body),
		}, nil
	}

	response := map[string]interface{}{
		"status":           "BOOKED",
		"confirmation_ref": appointment.ConfirmationRef,
		"appointment":      appointment,
	}

	body, _ := json.Marshal(response)
	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Headers:    headers,
		Body:       string(body),
	}, nil
}

func errorResponse(statusCode int, message string) events.APIGatewayProxyResponse {
	return events.APIGatewayProxyResponse{
		StatusCode: statusCode,
		Headers: map[string]string{
			"Content-Type":                 "application/json",
			"Access-Control-Allow-Origin":  "*",
			"Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
			"Access-Control-Allow-Headers": "Content-Type, Authorization",
		},
		Body: fmt.Sprintf(`{"error": "%s"}`, message),
	}
}

// Global appointment service instance
var appointmentService *AppointmentService

func main() {
	lambda.Start(lambdaHandler)
}