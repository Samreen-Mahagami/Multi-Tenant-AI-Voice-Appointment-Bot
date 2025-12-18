package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
)

// Appointment represents a booked appointment
type Appointment struct {
	ID            string    `json:"id"`
	TenantID      string    `json:"tenant_id"`
	SlotID        string    `json:"slot_id"`
	PatientName   string    `json:"patient_name"`
	PatientEmail  string    `json:"patient_email"`
	DoctorID      string    `json:"doctor_id"`
	DoctorName    string    `json:"doctor_name"`
	StartTime     time.Time `json:"start_time"`
	EndTime       time.Time `json:"end_time"`
	Status        string    `json:"status"`
	ConfirmationRef string  `json:"confirmation_ref"`
	CreatedAt     time.Time `json:"created_at"`
}

// Slot represents an available appointment slot
type Slot struct {
	SlotID     string    `json:"slot_id"`
	TenantID   string    `json:"tenant_id"`
	DoctorID   string    `json:"doctor_id"`
	DoctorName string    `json:"doctor_name"`
	StartTime  time.Time `json:"start_time"`
	EndTime    time.Time `json:"end_time"`
	Available  bool      `json:"available"`
}

// SearchSlotsRequest represents a slot search request
type SearchSlotsRequest struct {
	TenantID       string `json:"tenantId"`
	Date           string `json:"date"`
	TimePreference string `json:"timePreference"`
}

// ConfirmAppointmentRequest represents an appointment confirmation request
type ConfirmAppointmentRequest struct {
	TenantID     string `json:"tenantId"`
	SlotID       string `json:"slotId"`
	PatientName  string `json:"patientName"`
	PatientEmail string `json:"patientEmail"`
}

// AppointmentService handles appointment operations
type AppointmentService struct {
	appointments map[string]*Appointment // appointmentID -> appointment
	slots        map[string]*Slot        // slotID -> slot
}

// NewAppointmentService creates a new appointment service
func NewAppointmentService() *AppointmentService {
	service := &AppointmentService{
		appointments: make(map[string]*Appointment),
		slots:        make(map[string]*Slot),
	}

	// Initialize with some sample slots
	service.initializeSampleSlots()

	return service
}

// initializeSampleSlots creates sample appointment slots for testing
func (as *AppointmentService) initializeSampleSlots() {
	tenants := []string{"downtown_medical", "westside_family", "pediatric_care"}
	doctors := map[string][]map[string]string{
		"downtown_medical": {
			{"id": "dr_smith", "name": "Dr. Sarah Smith"},
			{"id": "dr_johnson", "name": "Dr. Michael Johnson"},
		},
		"westside_family": {
			{"id": "dr_patel", "name": "Dr. Priya Patel"},
			{"id": "dr_williams", "name": "Dr. James Williams"},
		},
		"pediatric_care": {
			{"id": "dr_brown", "name": "Dr. Emily Brown"},
			{"id": "dr_davis", "name": "Dr. Robert Davis"},
		},
	}

	// Generate slots for next 7 days
	baseTime := time.Now().Truncate(24 * time.Hour).Add(24 * time.Hour) // Tomorrow

	for _, tenantID := range tenants {
		tenantDoctors := doctors[tenantID]

		for day := 0; day < 7; day++ {
			currentDay := baseTime.Add(time.Duration(day) * 24 * time.Hour)

			// Skip weekends for simplicity
			if currentDay.Weekday() == time.Saturday || currentDay.Weekday() == time.Sunday {
				continue
			}

			for _, doctor := range tenantDoctors {
				// Morning slots: 9:00 AM - 12:00 PM (30-minute slots)
				for hour := 9; hour < 12; hour++ {
					for minute := 0; minute < 60; minute += 30 {
						startTime := time.Date(currentDay.Year(), currentDay.Month(), currentDay.Day(),
							hour, minute, 0, 0, currentDay.Location())
						endTime := startTime.Add(30 * time.Minute)

						slotID := fmt.Sprintf("%s-%s-%s", tenantID, doctor["id"], startTime.Format("20060102-1504"))

						as.slots[slotID] = &Slot{
							SlotID:     slotID,
							TenantID:   tenantID,
							DoctorID:   doctor["id"],
							DoctorName: doctor["name"],
							StartTime:  startTime,
							EndTime:    endTime,
							Available:  true,
						}
					}
				}

				// Afternoon slots: 2:00 PM - 5:00 PM (30-minute slots)
				for hour := 14; hour < 17; hour++ {
					for minute := 0; minute < 60; minute += 30 {
						startTime := time.Date(currentDay.Year(), currentDay.Month(), currentDay.Day(),
							hour, minute, 0, 0, currentDay.Location())
						endTime := startTime.Add(30 * time.Minute)

						slotID := fmt.Sprintf("%s-%s-%s", tenantID, doctor["id"], startTime.Format("20060102-1504"))

						as.slots[slotID] = &Slot{
							SlotID:     slotID,
							TenantID:   tenantID,
							DoctorID:   doctor["id"],
							DoctorName: doctor["name"],
							StartTime:  startTime,
							EndTime:    endTime,
							Available:  true,
						}
					}
				}
			}
		}
	}

	log.Printf("Initialized %d appointment slots", len(as.slots))
}

// SearchSlots finds available appointment slots
func (as *AppointmentService) SearchSlots(tenantID, date, timePreference string) ([]*Slot, error) {
	var targetDate time.Time
	var err error

	// Parse date
	switch strings.ToLower(date) {
	case "today":
		targetDate = time.Now().Truncate(24 * time.Hour)
	case "tomorrow":
		targetDate = time.Now().Truncate(24 * time.Hour).Add(24 * time.Hour)
	default:
		// Try to parse as date
		targetDate, err = time.Parse("2006-01-02", date)
		if err != nil {
			// Try other formats
			targetDate, err = time.Parse("01/02/2006", date)
			if err != nil {
				return nil, fmt.Errorf("invalid date format: %s", date)
			}
		}
	}

	var availableSlots []*Slot

	for _, slot := range as.slots {
		// Filter by tenant
		if slot.TenantID != tenantID {
			continue
		}

		// Filter by availability
		if !slot.Available {
			continue
		}

		// Filter by date
		if !isSameDay(slot.StartTime, targetDate) {
			continue
		}

		// Filter by time preference
		if timePreference != "" && timePreference != "any" {
			hour := slot.StartTime.Hour()
			switch strings.ToLower(timePreference) {
			case "morning":
				if hour < 9 || hour >= 12 {
					continue
				}
			case "afternoon":
				if hour < 12 || hour >= 17 {
					continue
				}
			case "evening":
				if hour < 17 || hour >= 20 {
					continue
				}
			}
		}

		availableSlots = append(availableSlots, slot)
	}

	// Limit to first 10 slots
	if len(availableSlots) > 10 {
		availableSlots = availableSlots[:10]
	}

	return availableSlots, nil
}

// ConfirmAppointment books an appointment
func (as *AppointmentService) ConfirmAppointment(tenantID, slotID, patientName, patientEmail string) (*Appointment, error) {
	// Find the slot
	slot, exists := as.slots[slotID]
	if !exists {
		return nil, fmt.Errorf("slot not found: %s", slotID)
	}

	// Check if slot belongs to tenant
	if slot.TenantID != tenantID {
		return nil, fmt.Errorf("slot does not belong to tenant: %s", tenantID)
	}

	// Check if slot is available
	if !slot.Available {
		return nil, fmt.Errorf("slot is no longer available: %s", slotID)
	}

	// Generate confirmation reference
	confirmationRef := generateConfirmationRef(tenantID)

	// Create appointment
	appointment := &Appointment{
		ID:              uuid.New().String(),
		TenantID:        tenantID,
		SlotID:          slotID,
		PatientName:     patientName,
		PatientEmail:    patientEmail,
		DoctorID:        slot.DoctorID,
		DoctorName:      slot.DoctorName,
		StartTime:       slot.StartTime,
		EndTime:         slot.EndTime,
		Status:          "CONFIRMED",
		ConfirmationRef: confirmationRef,
		CreatedAt:       time.Now(),
	}

	// Store appointment
	as.appointments[appointment.ID] = appointment

	// Mark slot as unavailable
	slot.Available = false

	return appointment, nil
}

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

// Utility functions

func isSameDay(t1, t2 time.Time) bool {
	y1, m1, d1 := t1.Date()
	y2, m2, d2 := t2.Date()
	return y1 == y2 && m1 == m2 && d1 == d2
}

func generateConfirmationRef(tenantID string) string {
	prefix := "APPT"
	if len(tenantID) >= 4 {
		prefix = strings.ToUpper(tenantID[:4])
	}

	timestamp := time.Now().Format("0102") // MMDD
	random := fmt.Sprintf("%03d", time.Now().Nanosecond()%1000)

	return fmt.Sprintf("%s-%s-%s", prefix, timestamp, random)
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