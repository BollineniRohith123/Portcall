#!/bin/bash

echo "🎙️ SIMULATING WESTPORTS AI VOICE AGENT DEMO"
echo "============================================="
echo ""

BACKEND_URL="https://0796086f-31e6-4512-b74d-a8a43b1bdc46.preview.emergentagent.com"

echo "📞 Simulating voice call: 'What's the status of container ABCD1234567?'"
curl -X POST "$BACKEND_URL/api/containers/status" \
  -H "Content-Type: application/json" \
  -d '{"containerNumber": "ABCD1234567"}' \
  -s > /dev/null

sleep 2

echo "📞 Simulating voice call: 'Update container EFGH9876543 to available for delivery'"
curl -X POST "$BACKEND_URL/api/containers/update" \
  -H "Content-Type: application/json" \
  -d '{"containerNumber": "EFGH9876543", "newStatus": "AVAILABLE_FOR_DELIVERY", "location": "Block B-10"}' \
  -s > /dev/null

sleep 2

echo "📞 Simulating voice call: 'Generate an eGatepass for container ABCD1234567 for ABC Logistics with truck WBE1234A'"
curl -X POST "$BACKEND_URL/api/gatepass/generate" \
  -H "Content-Type: application/json" \
  -d '{"containerNumber": "ABCD1234567", "haulierCompany": "ABC Logistics SDN BHD", "truckNumber": "WBE1234A"}' \
  -s > /dev/null

sleep 2

echo "📞 Simulating voice call: 'Check the schedule for vessel MSC MAYA'"
curl -X POST "$BACKEND_URL/api/vessels/schedule" \
  -H "Content-Type: application/json" \
  -d '{"vesselName": "MSC MAYA"}' \
  -s > /dev/null

sleep 2

echo "📞 Simulating voice call: 'Submit an ITT request for container MSKU7654321'"
curl -X POST "$BACKEND_URL/api/ssr/submit" \
  -H "Content-Type: application/json" \
  -d '{"containerNumber": "MSKU7654321", "ssrType": "ITT", "requestDetails": "Inter-terminal transfer required for vessel connection to Terminal 2"}' \
  -s > /dev/null

sleep 2

echo "📞 Simulating voice call: 'What is the status of container EFGH9876543?'"
curl -X POST "$BACKEND_URL/api/containers/status" \
  -H "Content-Type: application/json" \
  -d '{"containerNumber": "EFGH9876543"}' \
  -s > /dev/null

echo ""
echo "✅ Voice demonstration complete!"
echo "🌐 Check your dashboard at: http://localhost:3000"
echo "📊 All operations should appear in the Live Activities section"