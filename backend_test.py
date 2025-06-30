#!/usr/bin/env python3
import requests
import json
import websocket
import threading
import time
import unittest
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://0796086f-31e6-4512-b74d-a8a43b1bdc46.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"
WS_URL = f"wss://{BACKEND_URL.split('//')[1]}/ws"

# Sample container numbers for testing
SAMPLE_CONTAINERS = ["ABCD1234567", "EFGH9876543", "MSKU7654321"]
NON_EXISTENT_CONTAINER = "XXXX0000000"

# WebSocket message queue for testing real-time updates
ws_messages = []
ws_connected = False

def on_message(ws, message):
    """Callback for WebSocket messages"""
    print(f"WebSocket message received: {message}")
    ws_messages.append(json.loads(message))

def on_error(ws, error):
    """Callback for WebSocket errors"""
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    """Callback for WebSocket connection close"""
    print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    global ws_connected
    ws_connected = False

def on_open(ws):
    """Callback for WebSocket connection open"""
    print("WebSocket connection established")
    global ws_connected
    ws_connected = True

class WestportsBackendTest(unittest.TestCase):
    """Test suite for Westports AI Voice Agent Backend"""
    
    @classmethod
    def setUpClass(cls):
        """Set up WebSocket connection for real-time updates"""
        # Connect to WebSocket
        cls.ws = websocket.WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Start WebSocket connection in a separate thread
        cls.ws_thread = threading.Thread(target=cls.ws.run_forever)
        cls.ws_thread.daemon = True
        cls.ws_thread.start()
        
        # Wait for WebSocket connection to establish
        timeout = 5
        start_time = time.time()
        while not ws_connected and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not ws_connected:
            print("WARNING: WebSocket connection could not be established")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up WebSocket connection"""
        if hasattr(cls, 'ws'):
            cls.ws.close()
        
        if hasattr(cls, 'ws_thread'):
            cls.ws_thread.join(timeout=1)
    
    def setUp(self):
        """Clear WebSocket messages before each test"""
        global ws_messages
        ws_messages = []
    
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
            
            # Wait for WebSocket message
            time.sleep(1)
            
            # Verify WebSocket notification was sent
            ws_container_messages = [m for m in ws_messages if m["type"] == "containerQueried" and m["containerNumber"] == container]
            self.assertGreaterEqual(len(ws_container_messages), 1)
        
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
        
        # Wait for WebSocket message
        time.sleep(1)
        
        # Verify WebSocket notification was sent
        ws_update_messages = [m for m in ws_messages if m["type"] == "containerUpdated" and m["containerNumber"] == container]
        self.assertGreaterEqual(len(ws_update_messages), 1)
        self.assertEqual(ws_update_messages[-1]["oldStatus"], old_status)
        self.assertEqual(ws_update_messages[-1]["newStatus"], new_status)
        
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
        
        # Wait for WebSocket message
        time.sleep(1)
        
        # Verify WebSocket notification was sent
        ws_gatepass_messages = [m for m in ws_messages if m["type"] == "gatepassGenerated" and m["containerNumber"] == container]
        self.assertGreaterEqual(len(ws_gatepass_messages), 1)
        
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
        
        # Wait for WebSocket message
        time.sleep(1)
        
        # Verify WebSocket notification was sent
        ws_vessel_messages = [m for m in ws_messages if m["type"] == "vesselQueried" and m["vesselName"] == "MSC MAYA"]
        self.assertGreaterEqual(len(ws_vessel_messages), 1)
        
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
        
        # Wait for WebSocket message
        time.sleep(1)
        
        # Verify WebSocket notification was sent
        ws_ssr_messages = [m for m in ws_messages if m["type"] == "ssrSubmitted" and m["containerNumber"] == container]
        self.assertGreaterEqual(len(ws_ssr_messages), 1)
        
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

if __name__ == "__main__":
    print(f"Testing Westports AI Voice Agent Backend at {API_BASE_URL}")
    unittest.main(verbosity=2)