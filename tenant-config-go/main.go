// +build !lambda

package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gorilla/mux"
)

func (ts *TenantService) handleGetTenant(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	tenantName := vars["name"]

	tenant, err := ts.GetTenantByName(tenantName)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tenant)
}

// CORS middleware
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// Logging middleware
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.RequestURI, time.Since(start))
	})
}

func main() {
	// Get configuration file path
	configPath := os.Getenv("CONFIG_PATH")
	if configPath == "" {
		configPath = "tenants.yaml"
	}

	// Initialize tenant service
	tenantService, err := NewTenantService(configPath)
	if err != nil {
		log.Fatalf("Failed to initialize tenant service: %v", err)
	}

	log.Printf("Loaded %d tenants from %s", len(tenantService.config.Tenants), configPath)

	// Setup HTTP router
	r := mux.NewRouter()

	// Add middleware
	r.Use(corsMiddleware)
	r.Use(loggingMiddleware)

	// API routes
	api := r.PathPrefix("/v1").Subrouter()

	// Health check
	api.HandleFunc("/health", tenantService.handleHealth).Methods("GET")

	// Tenant operations
	api.HandleFunc("/tenants", tenantService.handleListTenants).Methods("GET")
	api.HandleFunc("/tenants/resolve", tenantService.handleResolveTenant).Methods("GET")
	api.HandleFunc("/tenants/{name}", tenantService.handleGetTenant).Methods("GET")

	// Get port from environment or default to 7001
	port := os.Getenv("PORT")
	if port == "" {
		port = "7001"
	}

	log.Printf("Starting Tenant Configuration Service on port %s", port)
	log.Printf("Available endpoints:")
	log.Printf("  GET /v1/health - Health check")
	log.Printf("  GET /v1/tenants - List all tenants")
	log.Printf("  GET /v1/tenants/{name} - Get tenant by name")
	log.Printf("  GET /v1/tenants/resolve?did={did} - Resolve tenant by DID")

	// Start server
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}