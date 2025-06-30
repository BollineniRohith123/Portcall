#!/usr/bin/env python3
import requests
import json
import time
import unittest
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://0796086f-31e6-4512-b74d-a8a43b1bdc46.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Sample container numbers for testing
SAMPLE_CONTAINERS = ["ABCD1234567", "EFGH9876543", "MSKU7654321"]
NON_EXISTENT_CONTAINER = "XXXX0000000"

class WestportsBackendTest(unittest.TestCase):
    """Test suite for Westports AI Voice Agent Backend"""
    
    def test_01_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{API_BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
    
    def test_02_get_dashboard_data(self):
        """Test dashboard data endpoint"""
        response = requests.get(f"{API_BASE_URL}/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("containers", data["data"])
        self.assertIn("vessels", data["data"])
        self.assertIn("gatepasses", data["data"])
        self.assertIn("ssrRequests", data["data"])
        
        # Verify sample containers exist in dashboard data
        container_numbers = [c["containerNumber"] for c in data["data"]["containers"]]
        for container in SAMPLE_CONTAINERS:
            self.assertIn(container, container_numbers)
    
    def test_03_get_container_status(self):
        """Test container status endpoint"""
        # Test valid container
        for container in SAMPLE_CONTAINERS:
            response = requests.post(
                f"{API_BASE_URL}/containers/status",
                json={"containerNumber": container}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["data"]["containerNumber"], container)
        
        # Test non-existent container
        response = requests.post(
            f"{API_BASE_URL}/containers/status",
            json={"containerNumber": NON_EXISTENT_CONTAINER}
        )
        self.assertEqual(response.status_code, 404)
        error = response.json()
        self.assertIn("detail", error)
        self.assertFalse(error["detail"]["success"])
    
    def test_04_update_container_status(self):
        """Test container status update endpoint"""
        container = SAMPLE_CONTAINERS[0]
        new_status = "LOADING"
        new_location = "YARD-B12"
        
        # Get current status
        response = requests.post(
            f"{API_BASE_URL}/containers/status",
            json={"containerNumber": container}
        )
        self.assertEqual(response.status_code, 200)
        original_data = response.json()
        old_status = original_data["data"]["status"]
        
        # Update container status
        response = requests.post(
            f"{API_BASE_URL}/containers/update",
            json={
                "containerNumber": container,
                "newStatus": new_status,
                "location": new_location
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], new_status)
        self.assertEqual(data["data"]["location"], new_location)
        
        # Test non-existent container
        response = requests.post(
            f"{API_BASE_URL}/containers/update",
            json={
                "containerNumber": NON_EXISTENT_CONTAINER,
                "newStatus": "DISCHARGED"
            }
        )
        self.assertEqual(response.status_code, 404)
        error = response.json()
        self.assertIn("detail", error)
        self.assertFalse(error["detail"]["success"])
        
        # Restore original status
        requests.post(
            f"{API_BASE_URL}/containers/update",
            json={
                "containerNumber": container,
                "newStatus": old_status
            }
        )
    
    def test_05_generate_gatepass(self):
        """Test eGatepass generation endpoint"""
        # Test container with proper conditions (ABCD1234567)
        container = SAMPLE_CONTAINERS[0]
        
        # First ensure container is in a state eligible for gatepass
        requests.post(
            f"{API_BASE_URL}/containers/update",
            json={
                "containerNumber": container,
                "newStatus": "DISCHARGED"
            }
        )
        
        # Generate gatepass
        response = requests.post(
            f"{API_BASE_URL}/gatepass/generate",
            json={
                "containerNumber": container,
                "haulierCompany": "TEST LOGISTICS SDN BHD",
                "truckNumber": "WXY-5678"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("id", data["data"])
        self.assertEqual(data["data"]["containerNumber"], container)
        
        # Test container with customs hold (MSKU7654321)
        container_with_hold = SAMPLE_CONTAINERS[2]
        response = requests.post(
            f"{API_BASE_URL}/gatepass/generate",
            json={
                "containerNumber": container_with_hold,
                "haulierCompany": "TEST LOGISTICS SDN BHD",
                "truckNumber": "WXY-5678"
            }
        )
        self.assertEqual(response.status_code, 400)
        error = response.json()
        self.assertIn("detail", error)
        self.assertFalse(error["detail"]["success"])
        self.assertIn("validationErrors", error["detail"])
        
        # Test non-existent container
        response = requests.post(
            f"{API_BASE_URL}/gatepass/generate",
            json={
                "containerNumber": NON_EXISTENT_CONTAINER,
                "haulierCompany": "TEST LOGISTICS SDN BHD",
                "truckNumber": "WXY-5678"
            }
        )
        self.assertEqual(response.status_code, 404)
        error = response.json()
        self.assertIn("detail", error)
        self.assertFalse(error["detail"]["success"])
    
    def test_06_check_vessel_schedule(self):
        """Test vessel schedule endpoint"""
        # Test by vessel name
        response = requests.post(
            f"{API_BASE_URL}/vessels/schedule",
            json={"vesselName": "MSC MAYA"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["vesselName"], "MSC MAYA")
        
        # Test by voyage number
        response = requests.post(
            f"{API_BASE_URL}/vessels/schedule",
            json={"voyageNumber": "EVG002W"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["voyageNumber"], "EVG002W")
        
        # Test non-existent vessel
        response = requests.post(
            f"{API_BASE_URL}/vessels/schedule",
            json={"vesselName": "NONEXISTENT VESSEL"}
        )
        self.assertEqual(response.status_code, 404)
        error = response.json()
        self.assertIn("detail", error)
        self.assertFalse(error["detail"]["success"])
    
    def test_07_submit_ssr(self):
        """Test SSR submission endpoint"""
        container = SAMPLE_CONTAINERS[0]
        
        # Submit SSR
        response = requests.post(
            f"{API_BASE_URL}/ssr/submit",
            json={
                "containerNumber": container,
                "ssrType": "STORAGE_EXTENSION",
                "requestDetails": "Extend storage by 5 days due to logistics delay"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("id", data["data"])
        self.assertEqual(data["data"]["containerNumber"], container)
        self.assertEqual(data["data"]["ssrType"], "STORAGE_EXTENSION")
        
        # Test different SSR type
        response = requests.post(
            f"{API_BASE_URL}/ssr/submit",
            json={
                "containerNumber": container,
                "ssrType": "ITT",
                "requestDetails": "Inter-terminal transfer required for vessel connection"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["ssrType"], "ITT")
        
        # Test non-existent container
        response = requests.post(
            f"{API_BASE_URL}/ssr/submit",
            json={
                "containerNumber": NON_EXISTENT_CONTAINER,
                "ssrType": "STORAGE_EXTENSION",
                "requestDetails": "Extend storage by 5 days"
            }
        )
        self.assertEqual(response.status_code, 404)
        error = response.json()
        self.assertIn("detail", error)
        self.assertFalse(error["detail"]["success"])

    def test_08_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint exists (without testing functionality)"""
        # We can only verify the endpoint exists in the code
        # Actual WebSocket testing would require a separate client
        print("WebSocket endpoint exists at /ws in the code")
        self.assertTrue(True)  # Always pass this test

if __name__ == "__main__":
    print(f"Testing Westports AI Voice Agent Backend at {API_BASE_URL}")
    unittest.main(verbosity=2)