package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

// Lambda handler function
func lambdaHandler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	log.Printf("Received request: %s %s", request.HTTPMethod, request.Path)

	// Initialize tenant service if not already done
	if tenantService == nil {
		var err error
		tenantService, err = NewTenantService("tenants.yaml")
		if err != nil {
			log.Printf("Failed to initialize tenant service: %v", err)
			return errorResponse(500, fmt.Sprintf("Service initialization failed: %v", err)), nil
		}
		log.Printf("Tenant service initialized with %d tenants", len(tenantService.config.Tenants))
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

	case request.Path == "/v1/tenants" && request.HTTPMethod == "GET":
		return handleListTenantsLambda(headers)

	case request.Path == "/v1/tenants/resolve" && request.HTTPMethod == "GET":
		return handleResolveTenantsLambda(request, headers)

	case strings.HasPrefix(request.Path, "/v1/tenants/") && request.HTTPMethod == "GET":
		// Extract tenant name from path
		parts := strings.Split(request.Path, "/")
		if len(parts) >= 4 {
			tenantName := parts[3]
			return handleGetTenantLambda(tenantName, headers)
		}
		return errorResponse(400, "Invalid tenant path"), nil

	default:
		return errorResponse(404, "Not found"), nil
	}
}

func handleHealthLambda(headers map[string]string) (events.APIGatewayProxyResponse, error) {
	response := map[string]interface{}{
		"status":    "healthy",
		"service":   "tenant-config-service",
		"timestamp": "2025-12-18T10:00:00Z",
		"tenants":   len(tenantService.config.Tenants),
	}

	body, _ := json.Marshal(response)
	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Headers:    headers,
		Body:       string(body),
	}, nil
}

func handleListTenantsLambda(headers map[string]string) (events.APIGatewayProxyResponse, error) {
	tenants := tenantService.GetAllTenants()

	tenantList := make([]map[string]interface{}, 0, len(tenants))
	for name, tenant := range tenants {
		tenantList = append(tenantList, map[string]interface{}{
			"name":         name,
			"display_name": tenant.DisplayName,
			"did":          tenant.DID,
			"specialties":  tenant.Specialties,
		})
	}

	response := map[string]interface{}{
		"tenants": tenantList,
		"count":   len(tenantList),
	}

	body, _ := json.Marshal(response)
	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Headers:    headers,
		Body:       string(body),
	}, nil
}

func handleResolveTenantsLambda(request events.APIGatewayProxyRequest, headers map[string]string) (events.APIGatewayProxyResponse, error) {
	did := request.QueryStringParameters["did"]
	if did == "" {
		return errorResponse(400, "DID parameter is required"), nil
	}

	tenant, err := tenantService.GetTenantByDID(did)
	if err != nil {
		return errorResponse(404, err.Error()), nil
	}

	body, _ := json.Marshal(tenant)
	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Headers:    headers,
		Body:       string(body),
	}, nil
}

func handleGetTenantLambda(tenantName string, headers map[string]string) (events.APIGatewayProxyResponse, error) {
	// URL decode the tenant name
	decodedName, err := url.QueryUnescape(tenantName)
	if err != nil {
		decodedName = tenantName
	}

	tenant, err := tenantService.GetTenantByName(decodedName)
	if err != nil {
		return errorResponse(404, err.Error()), nil
	}

	body, _ := json.Marshal(tenant)
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

// Global tenant service instance
var tenantService *TenantService

func init() {
	// Lambda will call lambdaHandler directly
}