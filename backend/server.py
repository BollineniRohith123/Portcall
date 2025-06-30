from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime, timedelta
import uuid
import os
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(mongo_url)
db = client.westports_db

app = FastAPI(title="Westports AI Voice Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class ContainerStatus(BaseModel):
    containerNumber: str

class ContainerUpdate(BaseModel):
    containerNumber: str
    newStatus: str
    location: Optional[str] = None

class GatepassRequest(BaseModel):
    containerNumber: str
    haulierCompany: str
    truckNumber: str

class VesselScheduleRequest(BaseModel):
    vesselName: Optional[str] = None
    voyageNumber: Optional[str] = None

class SSRRequest(BaseModel):
    containerNumber: str
    ssrType: str
    requestDetails: str

# Initialize database with sample data
def initialize_database():
    # Check if data already exists
    if db.containers.count_documents({}) > 0:
        return
    
    # Sample containers data
    containers_data = [
        {
            "id": str(uuid.uuid4()),
            "containerNumber": "ABCD1234567",
            "status": "DISCHARGED",
            "location": "Block A-15",
            "vesselName": "MSC MAYA",
            "voyageNumber": "MAY001E",
            "arrivalDate": "2025-06-28",
            "dischargeDate": "2025-06-29",
            "containerType": "DV",
            "size": "40HC",
            "weight": "28500",
            "availableForPickup": True,
            "charges": 450.00,
            "currency": "MYR",
            "edoStatus": "RELEASED",
            "customsStatus": "CLEARED",
            "activeGatepass": None,
            "lastUpdated": datetime.utcnow().isoformat(),
            "consignee": "ABC TRADING SDN BHD",
            "shippingAgent": "MAERSK MALAYSIA",
            "portOfLoading": "SINGAPORE",
            "ssrHistory": []
        },
        {
            "id": str(uuid.uuid4()),
            "containerNumber": "EFGH9876543",
            "status": "ARRIVED",
            "location": "Block B-08",
            "vesselName": "EVERGREEN STAR",
            "voyageNumber": "EVG002W",
            "arrivalDate": "2025-06-29",
            "dischargeDate": None,
            "containerType": "RF",
            "size": "20ST",
            "weight": "18200",
            "availableForPickup": False,
            "charges": 320.00,
            "currency": "MYR",
            "edoStatus": "PENDING",
            "customsStatus": "PENDING",
            "activeGatepass": None,
            "lastUpdated": datetime.utcnow().isoformat(),
            "consignee": "XYZ LOGISTICS",
            "shippingAgent": "EVERGREEN SHIPPING",
            "portOfLoading": "HONG KONG",
            "ssrHistory": []
        },
        {
            "id": str(uuid.uuid4()),
            "containerNumber": "MSKU7654321",
            "status": "CUSTOMS_HOLD",
            "location": "CIC-01",
            "vesselName": "MSC MEDITERRANEAN",
            "voyageNumber": "MED003E",
            "arrivalDate": "2025-06-27",
            "dischargeDate": "2025-06-28",
            "containerType": "DV",
            "size": "40ST",
            "weight": "25800",
            "availableForPickup": False,
            "charges": 680.00,
            "currency": "MYR",
            "edoStatus": "RELEASED",
            "customsStatus": "HOLD",
            "activeGatepass": None,
            "lastUpdated": datetime.utcnow().isoformat(),
            "consignee": "GLOBAL IMPORTS",
            "shippingAgent": "MSC MALAYSIA",
            "portOfLoading": "ROTTERDAM",
            "ssrHistory": []
        }
    ]
    
    # Insert containers
    db.containers.insert_many(containers_data)
    
    # Sample vessels data
    vessels_data = [
        {
            "id": str(uuid.uuid4()),
            "vesselName": "MSC MAYA",
            "imoNumber": "9876543",
            "voyageNumber": "MAY001E",
            "eta": "2025-06-28T06:00:00Z",
            "etd": "2025-07-02T18:00:00Z",
            "berth": "CT1-B3",
            "status": "ALONGSIDE",
            "agent": "MAERSK MALAYSIA"
        },
        {
            "id": str(uuid.uuid4()),
            "vesselName": "EVERGREEN STAR",
            "imoNumber": "9765432",
            "voyageNumber": "EVG002W",
            "eta": "2025-06-29T14:00:00Z",
            "etd": "2025-07-03T22:00:00Z",
            "berth": "CT2-B1",
            "status": "DISCHARGING",
            "agent": "EVERGREEN SHIPPING"
        }
    ]
    
    db.vessels.insert_many(vessels_data)

# Initialize database on startup
initialize_database()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Ultravox Tool Endpoints
@app.post("/api/containers/status")
async def get_container_status(request: ContainerStatus):
    """Ultravox tool: Get container status from ETP/OPUS system"""
    print(f"🔍 Tool Call: getContainerStatus for {request.containerNumber}")
    
    container = db.containers.find_one({"containerNumber": request.containerNumber})
    
    if container:
        # Remove MongoDB ObjectId for JSON serialization
        container.pop('_id', None)
        
        # Emit real-time update to frontend
        await manager.broadcast({
            "type": "containerQueried",
            "containerNumber": request.containerNumber,
            "timestamp": datetime.utcnow().isoformat(),
            "data": container,
            "action": "STATUS_QUERY"
        })
        
        return {
            "success": True,
            "data": container,
            "message": f"Container {request.containerNumber} found successfully in ETP system",
            "systemSource": "ETP/OPUS"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"Container {request.containerNumber} not found in our ETP/OPUS system. Please verify the container number format (ABCD1234567).",
                "systemSource": "ETP/OPUS"
            }
        )

@app.post("/api/containers/update")
async def update_container_status(request: ContainerUpdate):
    """Ultravox tool: Update container status in OPUS system"""
    print(f"🔄 Tool Call: updateContainerStatus for {request.containerNumber} to {request.newStatus}")
    
    container = db.containers.find_one({"containerNumber": request.containerNumber})
    
    if container:
        old_status = container["status"]
        
        # Update container
        update_data = {
            "status": request.newStatus,
            "lastUpdated": datetime.utcnow().isoformat(),
            "availableForPickup": request.newStatus in ["DISCHARGED", "AVAILABLE_FOR_DELIVERY"]
        }
        
        if request.location:
            update_data["location"] = request.location
            
        # Status-specific updates
        if request.newStatus == "GATED_OUT":
            update_data["gateOutTime"] = datetime.utcnow().isoformat()
            update_data["availableForPickup"] = False
        
        db.containers.update_one(
            {"containerNumber": request.containerNumber},
            {"$set": update_data}
        )
        
        # Get updated container
        updated_container = db.containers.find_one({"containerNumber": request.containerNumber})
        updated_container.pop('_id', None)
        
        # Emit real-time update to frontend
        await manager.broadcast({
            "type": "containerUpdated",
            "containerNumber": request.containerNumber,
            "oldStatus": old_status,
            "newStatus": request.newStatus,
            "timestamp": datetime.utcnow().isoformat(),
            "data": updated_container,
            "action": "STATUS_UPDATE"
        })
        
        return {
            "success": True,
            "data": updated_container,
            "message": f"Container {request.containerNumber} successfully updated from {old_status} to {request.newStatus} in OPUS system",
            "systemSource": "OPUS/ETP"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"Container {request.containerNumber} not found in our system",
                "systemSource": "OPUS/ETP"
            }
        )

@app.post("/api/gatepass/generate")
async def generate_gatepass(request: GatepassRequest):
    """Ultravox tool: Generate eGatepass through ETP system"""
    print(f"📋 Tool Call: generateEGatepass for {request.containerNumber} by {request.haulierCompany}")
    
    container = db.containers.find_one({"containerNumber": request.containerNumber})
    
    if not container:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"Container {request.containerNumber} not found in ETP system"
            }
        )
    
    # Validation checks
    validation_errors = []
    
    if container["edoStatus"] != "RELEASED":
        validation_errors.append("EDO not released by shipping agent")
    
    if container["customsStatus"] != "CLEARED":
        validation_errors.append("Customs clearance pending")
    
    if not container["availableForPickup"]:
        validation_errors.append(f"Container status {container['status']} not eligible for pickup")
    
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Cannot generate eGatepass: {', '.join(validation_errors)}",
                "validationErrors": validation_errors,
                "systemSource": "ETP"
            }
        )
    
    # Generate gatepass
    gatepass_id = f"GP{int(datetime.utcnow().timestamp())}"
    valid_until = datetime.utcnow() + timedelta(hours=48)
    
    gatepass = {
        "id": gatepass_id,
        "containerNumber": request.containerNumber,
        "haulierCompany": request.haulierCompany,
        "truckNumber": request.truckNumber,
        "generatedAt": datetime.utcnow().isoformat(),
        "validUntil": valid_until.isoformat(),
        "status": "ACTIVE",
        "generatedBy": "AISHA_AI_AGENT",
        "charges": container["charges"],
        "containerDetails": {
            "type": container["containerType"],
            "size": container["size"],
            "weight": container["weight"],
            "location": container["location"]
        }
    }
    
    # Save gatepass
    db.gatepasses.insert_one(gatepass.copy())
    
    # Update container with active gatepass
    db.containers.update_one(
        {"containerNumber": request.containerNumber},
        {"$set": {"activeGatepass": gatepass_id}}
    )
    
    # Emit real-time update to frontend
    await manager.broadcast({
        "type": "gatepassGenerated",
        "gatepass": gatepass,
        "containerNumber": request.containerNumber,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "GATEPASS_GENERATED"
    })
    
    return {
        "success": True,
        "data": gatepass,
        "message": f"eGatepass {gatepass_id} generated successfully for container {request.containerNumber}. Valid until {valid_until.strftime('%Y-%m-%d %H:%M:%S')}",
        "systemSource": "ETP"
    }

@app.post("/api/vessels/schedule")
async def check_vessel_schedule(request: VesselScheduleRequest):
    """Ultravox tool: Check vessel schedule from CBAS system"""
    print(f"🚢 Tool Call: checkVesselSchedule for {request.vesselName or request.voyageNumber}")
    
    query = {}
    if request.vesselName:
        query["vesselName"] = {"$regex": request.vesselName, "$options": "i"}
    elif request.voyageNumber:
        query["voyageNumber"] = request.voyageNumber.upper()
    
    vessel = db.vessels.find_one(query)
    
    if vessel:
        vessel.pop('_id', None)
        
        await manager.broadcast({
            "type": "vesselQueried",
            "vesselName": vessel["vesselName"],
            "timestamp": datetime.utcnow().isoformat(),
            "data": vessel,
            "action": "VESSEL_SCHEDULE_QUERY"
        })
        
        return {
            "success": True,
            "data": vessel,
            "message": "Vessel schedule information retrieved from CBAS system",
            "systemSource": "CBAS"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Vessel not found in CBAS system. Please check vessel name or voyage number.",
                "systemSource": "CBAS"
            }
        )

@app.post("/api/ssr/submit")
async def submit_ssr(request: SSRRequest):
    """Ultravox tool: Submit Special Service Request to ETP system"""
    print(f"📝 Tool Call: submitSSR for {request.containerNumber} - {request.ssrType}")
    
    container = db.containers.find_one({"containerNumber": request.containerNumber})
    
    if not container:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": f"Container {request.containerNumber} not found in ETP system"
            }
        )
    
    ssr_id = f"SSR{int(datetime.utcnow().timestamp())}"
    ssr = {
        "id": ssr_id,
        "containerNumber": request.containerNumber,
        "ssrType": request.ssrType,
        "requestDetails": request.requestDetails,
        "status": "SUBMITTED",
        "submittedAt": datetime.utcnow().isoformat(),
        "submittedBy": "AISHA_AI_AGENT",
        "expectedProcessingTime": "24-48 hours"
    }
    
    # Save SSR
    db.ssr_requests.insert_one(ssr.copy())
    
    # Update container SSR history
    db.containers.update_one(
        {"containerNumber": request.containerNumber},
        {"$push": {"ssrHistory": ssr_id}}
    )
    
    # Emit real-time update
    await manager.broadcast({
        "type": "ssrSubmitted",
        "ssr": ssr,
        "containerNumber": request.containerNumber,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "SSR_SUBMITTED"
    })
    
    return {
        "success": True,
        "data": ssr,
        "message": f"SSR {ssr_id} submitted successfully for {request.ssrType}. Expected processing time: 24-48 hours",
        "systemSource": "ETP"
    }

# Dashboard API
@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get all dashboard data"""
    containers = list(db.containers.find({}, {"_id": 0}))
    vessels = list(db.vessels.find({}, {"_id": 0}))
    gatepasses = list(db.gatepasses.find({}, {"_id": 0}))
    ssr_requests = list(db.ssr_requests.find({}, {"_id": 0}))
    
    return {
        "success": True,
        "data": {
            "containers": containers,
            "vessels": vessels,
            "gatepasses": gatepasses,
            "ssrRequests": ssr_requests
        }
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)