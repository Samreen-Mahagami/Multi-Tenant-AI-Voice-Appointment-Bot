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

// Types are defined in types.go

// Service methods are defined in types.go

// HTTP Handlers

func (as *AppointmentService) handleHealth(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":       "healthy",
		"service":      "appointment-service",
		"timestamp":    time.Now().UTC(),
		"appointments": len(as.appointments),
		"slots":        len(as.slots),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (as *AppointmentService) handleSearchSlots(w http.ResponseWriter, r *http.Request) {
	var req SearchSlotsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	slots, err := as.SearchSlots(req.TenantID, req.Date, req.TimePreference)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	response := map[string]interface{}{
		"slots": slots,
		"count": len(slots),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (as *AppointmentService) handleConfirmAppointment(w http.ResponseWriter, r *http.Request) {
	var req ConfirmAppointmentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	appointment, err := as.ConfirmAppointment(req.TenantID, req.SlotID, req.PatientName, req.PatientEmail)
	if err != nil {
		response := map[string]interface{}{
			"status": "FAILED",
			"error":  err.Error(),
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(response)
		return
	}

	response := map[string]interface{}{
		"status":           "BOOKED",
		"confirmation_ref": appointment.ConfirmationRef,
		"appointment":      appointment,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Utility functions are defined in types.go

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
	// Initialize appointment service
	appointmentService := NewAppointmentService()

	// Setup HTTP router
	r := mux.NewRouter()

	// Add middleware
	r.Use(corsMiddleware)
	r.Use(loggingMiddleware)

	// API routes
	api := r.PathPrefix("/v1").Subrouter()

	// Health check
	api.HandleFunc("/health", appointmentService.handleHealth).Methods("GET")

	// Appointment operations
	api.HandleFunc("/slots/search", appointmentService.handleSearchSlots).Methods("POST")
	api.HandleFunc("/appointments/confirm", appointmentService.handleConfirmAppointment).Methods("POST")

	// Get port from environment or default to 7002
	port := os.Getenv("PORT")
	if port == "" {
		port = "7002"
	}

	log.Printf("Starting Appointment Service on port %s", port)
	log.Printf("Available endpoints:")
	log.Printf("  GET /v1/health - Health check")
	log.Printf("  POST /v1/slots/search - Search available slots")
	log.Printf("  POST /v1/appointments/confirm - Confirm appointment")

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