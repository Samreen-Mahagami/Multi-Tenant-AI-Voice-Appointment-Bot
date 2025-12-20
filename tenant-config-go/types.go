package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"

	"gopkg.in/yaml.v3"
)

// Tenant represents a medical clinic configuration
type Tenant struct {
	DID           string    `yaml:"did" json:"did"`
	Name          string    `yaml:"name" json:"name"`
	DisplayName   string    `yaml:"display_name" json:"display_name"`
	Greeting      string    `yaml:"greeting" json:"greeting"`
	PollyVoiceID  string    `yaml:"polly_voice_id" json:"polly_voice_id"`
	PollyEngine   string    `yaml:"polly_engine" json:"polly_engine"`
	BusinessHours string    `yaml:"business_hours" json:"business_hours"`
	Timezone      string    `yaml:"timezone" json:"timezone"`
	Specialties   []string  `yaml:"specialties" json:"specialties"`
	Doctors       []Doctor  `yaml:"doctors" json:"doctors"`
	Contact       Contact   `yaml:"contact" json:"contact"`
}

// Doctor represents a doctor in the clinic
type Doctor struct {
	Name      string `yaml:"name" json:"name"`
	Specialty string `yaml:"specialty" json:"specialty"`
	ID        string `yaml:"id" json:"id"`
}

// Contact represents clinic contact information
type Contact struct {
	Phone   string `yaml:"phone" json:"phone"`
	Email   string `yaml:"email" json:"email"`
	Address string `yaml:"address" json:"address"`
}

// TenantsConfig represents the entire configuration file
type TenantsConfig struct {
	Tenants map[string]Tenant `yaml:"tenants"`
}

// TenantService handles tenant operations
type TenantService struct {
	config    *TenantsConfig
	didToName map[string]string // DID -> tenant name mapping
}

// NewTenantService creates a new tenant service
func NewTenantService(configPath string) (*TenantService, error) {
	data, err := ioutil.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config TenantsConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	// Build DID to tenant name mapping
	didToName := make(map[string]string)
	for tenantName, tenant := range config.Tenants {
		didToName[tenant.DID] = tenantName
	}

	return &TenantService{
		config:    &config,
		didToName: didToName,
	}, nil
}

// GetTenantByDID returns tenant configuration by DID
func (ts *TenantService) GetTenantByDID(did string) (*Tenant, error) {
	tenantName, exists := ts.didToName[did]
	if !exists {
		return nil, fmt.Errorf("tenant not found for DID: %s", did)
	}

	tenant := ts.config.Tenants[tenantName]
	return &tenant, nil
}

// GetTenantByName returns tenant configuration by name
func (ts *TenantService) GetTenantByName(name string) (*Tenant, error) {
	tenant, exists := ts.config.Tenants[name]
	if !exists {
		return nil, fmt.Errorf("tenant not found: %s", name)
	}

	return &tenant, nil
}

// GetAllTenants returns all tenant configurations
func (ts *TenantService) GetAllTenants() map[string]Tenant {
	return ts.config.Tenants
}

// HTTP Handlers for regular HTTP server

func (ts *TenantService) handleHealth(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":    "healthy",
		"service":   "tenant-config-service",
		"timestamp": time.Now().UTC(),
		"tenants":   len(ts.config.Tenants),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (ts *TenantService) handleResolveTenant(w http.ResponseWriter, r *http.Request) {
	did := r.URL.Query().Get("did")
	if did == "" {
		http.Error(w, "DID parameter is required", http.StatusBadRequest)
		return
	}

	tenant, err := ts.GetTenantByDID(did)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tenant)
}

// handleGetTenant is implemented in main.go for HTTP server

func (ts *TenantService) handleListTenants(w http.ResponseWriter, r *http.Request) {
	tenants := ts.GetAllTenants()

	// Return just the basic info for listing
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

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}