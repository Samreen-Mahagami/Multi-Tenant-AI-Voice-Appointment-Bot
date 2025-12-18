#!/usr/bin/env python3
"""
Phase 5: Backend Integration Testing (without Bedrock Agent)
Tests the complete multi-tenant backend system integration.
"""

import json
import requests
from datetime import datetime, timedelta
import time

# Service URLs (deployed Lambda functions)
TENANT_CONFIG_URL = 'https://3ecpj0ss4j.execute-api.us-east-1.amazonaws.com/prod'
APPOINTMENT_SERVICE_URL = 'https://zkbwkpdpx9.execute-api.us-east-1.amazonaws.com/prod'

class BackendIntegrationTester:
    def __init__(self):
        pass
        
    def test_complete_appointment_flow(self):
        """Test the complete appointment booking workflow"""
        print("🔄 Testing Complete Appointment Booking Workflow")
        print("=" * 50)
        
        # Step 1: Resolve tenant by DID (simulating voice call routing)
        print("1️⃣  Resolving tenant by DID 1001...")
        tenant_response = requests.get(f"{TENANT_CONFIG_URL}/v1/tenants/resolve?did=1001")
        
        if tenant_response.status_code != 200:
            print(f"❌ Tenant resolution failed: {tenant_response.status_code}")
            return False
            
        tenant = tenant_response.json()
        print(f"✅ Resolved: {tenant['name']}")
        print(f"   Greeting: {tenant['greeting']}")
        print(f"   Doctors: {[d['name'] for d in tenant['doctors']]}")
        
        # Step 2: Search for available appointment slots
        print("\n2️⃣  Searching for available appointment slots...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        search_payload = {
            "tenantId": "downtown_medical",
            "date": "tomorrow",
            "timePreference": "morning"
        }
        
        search_response = requests.post(
            f"{APPOINTMENT_SERVICE_URL}/v1/slots/search",
            json=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if search_response.status_code != 200:
            print(f"❌ Slot search failed: {search_response.status_code}")
            return False
            
        search_data = search_response.json()
        slots = search_data.get('slots', [])
        
        if not slots:
            print("❌ No slots available")
            return False
            
        print(f"✅ Found {len(slots)} available slots")
        selected_slot = slots[0]
        print(f"   Selected: {selected_slot['doctor_name']} at {selected_slot['start_time']}")
        
        # Step 3: Book the appointment
        print("\n3️⃣  Booking the appointment...")
        
        booking_payload = {
            "tenantId": "downtown_medical",
            "slotId": selected_slot['slot_id'],
            "patientName": "John Smith",
            "patientEmail": "john.smith@email.com"
        }
        
        booking_response = requests.post(
            f"{APPOINTMENT_SERVICE_URL}/v1/appointments/confirm",
            json=booking_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if booking_response.status_code != 200:
            print(f"❌ Booking failed: {booking_response.status_code} - {booking_response.text}")
            return False
            
        booking_data = booking_response.json()
        appointment = booking_data['appointment']
        
        print(f"✅ Appointment booked successfully!")
        print(f"   Confirmation: {appointment['confirmation_ref']}")
        print(f"   Patient: {appointment['patient_name']}")
        print(f"   Doctor: {appointment['doctor_name']}")
        print(f"   Time: {appointment['start_time']}")
        print(f"   Status: {appointment['status']}")
        
        # Step 4: Verify slot is no longer available
        print("\n4️⃣  Verifying slot is no longer available...")
        
        # Search again for the same slot
        verify_response = requests.post(
            f"{APPOINTMENT_SERVICE_URL}/v1/slots/search",
            json=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            verify_slots = verify_data.get('slots', [])
            
            # Check if the booked slot is still in available slots
            booked_slot_still_available = any(
                slot['slot_id'] == selected_slot['slot_id'] 
                for slot in verify_slots
            )
            
            if booked_slot_still_available:
                print("❌ Booked slot is still showing as available (double-booking risk)")
                return False
            else:
                print("✅ Booked slot is no longer available (double-booking prevented)")
        
        return True
    
    def test_multi_tenant_isolation(self):
        """Test that tenants can only see their own data"""
        print("\n🏥 Testing Multi-Tenant Isolation")
        print("=" * 40)
        
        tenants = [
            {"id": "downtown_medical", "name": "Downtown Medical"},
            {"id": "westside_family", "name": "Westside Family"},
            {"id": "pediatric_care", "name": "Pediatric Care"}
        ]
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        for tenant in tenants:
            print(f"\n🔍 Testing {tenant['name']}...")
            
            search_payload = {
                "tenantId": tenant['id'],
                "date": "tomorrow",
                "timePreference": "any"
            }
            
            response = requests.post(
                f"{APPOINTMENT_SERVICE_URL}/v1/slots/search",
                json=search_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                slots = data.get('slots', [])
                
                # Verify all slots belong to this tenant
                foreign_slots = [
                    slot for slot in slots 
                    if slot['tenant_id'] != tenant['id']
                ]
                
                if foreign_slots:
                    print(f"❌ Found {len(foreign_slots)} slots from other tenants!")
                    return False
                else:
                    print(f"✅ All {len(slots)} slots belong to {tenant['name']}")
            else:
                print(f"❌ Search failed: {response.status_code}")
                return False
        
        return True
    
    def test_business_hours_validation(self):
        """Test that appointments respect business hours"""
        print("\n⏰ Testing Business Hours Validation")
        print("=" * 40)
        
        search_payload = {
            "tenantId": "downtown_medical",
            "date": "tomorrow",
            "timePreference": "any"
        }
        
        response = requests.post(
            f"{APPOINTMENT_SERVICE_URL}/v1/slots/search",
            json=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.status_code}")
            return False
            
        data = response.json()
        slots = data.get('slots', [])
        
        business_hours_violations = []
        
        for slot in slots:
            start_time = datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00'))
            hour = start_time.hour
            
            # Business hours: 9 AM - 5 PM (9-17 in 24h format)
            if hour < 9 or hour >= 17:
                business_hours_violations.append(slot)
        
        if business_hours_violations:
            print(f"❌ Found {len(business_hours_violations)} slots outside business hours")
            for violation in business_hours_violations[:3]:  # Show first 3
                print(f"   {violation['start_time']} - {violation['doctor_name']}")
            return False
        else:
            print(f"✅ All {len(slots)} slots are within business hours (9 AM - 5 PM)")
            return True
    
    def test_error_handling(self):
        """Test error scenarios and edge cases"""
        print("\n⚠️  Testing Error Handling")
        print("=" * 30)
        
        # Test 1: Invalid tenant DID
        print("1. Testing invalid tenant DID...")
        response = requests.get(f"{TENANT_CONFIG_URL}/v1/tenants/resolve?did=9999")
        if response.status_code == 404:
            print("✅ Invalid DID properly rejected")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            return False
        
        # Test 2: Invalid slot booking
        print("2. Testing invalid slot booking...")
        invalid_booking = {
            "tenantId": "downtown_medical",
            "slotId": "invalid-slot-id",
            "patientName": "Test Patient",
            "patientEmail": "test@example.com"
        }
        
        response = requests.post(
            f"{APPOINTMENT_SERVICE_URL}/v1/appointments/confirm",
            json=invalid_booking,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code >= 400:
            print("✅ Invalid slot booking properly rejected")
        else:
            print(f"❌ Expected error, got {response.status_code}")
            return False
        
        # Test 3: Cross-tenant booking attempt
        print("3. Testing cross-tenant booking attempt...")
        
        # First, get a slot from westside_family
        search_payload = {
            "tenantId": "westside_family",
            "date": "tomorrow",
            "timePreference": "morning"
        }
        
        search_response = requests.post(
            f"{APPOINTMENT_SERVICE_URL}/v1/slots/search",
            json=search_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            slots = search_data.get('slots', [])
            
            if slots:
                westside_slot = slots[0]
                
                # Try to book it as downtown_medical
                cross_tenant_booking = {
                    "tenantId": "downtown_medical",  # Wrong tenant!
                    "slotId": westside_slot['slot_id'],
                    "patientName": "Test Patient",
                    "patientEmail": "test@example.com"
                }
                
                response = requests.post(
                    f"{APPOINTMENT_SERVICE_URL}/v1/appointments/confirm",
                    json=cross_tenant_booking,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code >= 400:
                    print("✅ Cross-tenant booking properly rejected")
                else:
                    print(f"❌ Cross-tenant booking should be rejected, got {response.status_code}")
                    return False
        
        return True
    
    def run_full_backend_test(self):
        """Run the complete backend integration test suite"""
        print("🚀 Phase 5: Backend Integration Testing")
        print("=" * 60)
        
        tests = [
            ("Complete Appointment Flow", self.test_complete_appointment_flow),
            ("Multi-Tenant Isolation", self.test_multi_tenant_isolation),
            ("Business Hours Validation", self.test_business_hours_validation),
            ("Error Handling", self.test_error_handling)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 BACKEND INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        overall_success = all(results.values())
        print(f"\nOverall Backend Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        
        if overall_success:
            print("\n🎉 Backend Integration Complete!")
            print("   ✅ Multi-tenant routing working")
            print("   ✅ Appointment booking functional") 
            print("   ✅ Data isolation maintained")
            print("   ✅ Business rules enforced")
            print("   ✅ Error handling validated")
            print("\n📋 Ready for voice integration with Bedrock Agent!")
        
        return overall_success

if __name__ == "__main__":
    tester = BackendIntegrationTester()
    tester.run_full_backend_test()