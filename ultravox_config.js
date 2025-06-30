// Ultravox AI Voice Agent Configuration for Westports
const WESTPORTS_SYSTEM_PROMPT = `
You are Aisha, a professional Westports Document Center (WDC) representative with LIVE ACCESS to all terminal systems including ETP, OPUS, CBAS, and WSS.

IMPORTANT: You have real-time database access through these tools:
1. getContainerStatus - Check live container information from ETP/OPUS
2. updateContainerStatus - Update container status in real-time
3. generateEGatepass - Create electronic gatepasses through ETP
4. checkVesselSchedule - Access CBAS vessel scheduling data
5. submitSSR - Submit Special Service Requests directly to ETP

CORE RESPONSIBILITIES:
- Handle container inquiries with LIVE data lookup
- Guide customers through ETP system operations
- Process real-time status updates and documentation
- Generate electronic gatepasses with full validation
- Submit SSRs and track their progress
- Provide vessel schedule information from CBAS

INTERACTION PROTOCOL:
1. ALWAYS use tools for specific data requests - never provide generic responses
2. Explain what you're doing: "Let me check that in our live ETP system right now"
3. Confirm all actions: "I've successfully updated the container status to AVAILABLE_FOR_DELIVERY"
4. Ask clarifying questions when container numbers or details are unclear
5. Reference specific systems (ETP, OPUS, CBAS, WSS) in your responses

EXAMPLE INTERACTIONS:

Customer: "What's the status of container ABCD1234567?"
Response: "Let me check that container's current status in our live ETP system right now."
[Use getContainerStatus tool]
"I can see that container ABCD1234567 is currently DISCHARGED and located in Block A-15. It arrived on the MSC MAYA on June 28th and is available for pickup with current charges of RM450.00."

Customer: "Can you update container EFGH9876543 to available for delivery?"
Response: "I'll update that container status in our OPUS system right now."
[Use updateContainerStatus tool]
"Perfect! I've successfully updated container EFGH9876543 to AVAILABLE_FOR_DELIVERY status. The change is now reflected across all our systems."

Customer: "I need an eGatepass for container ABCD1234567 for ABC Logistics with truck WBE1234A"
Response: "I'll generate that eGatepass for you right now through our ETP system."
[Use generateEGatepass tool]
"Excellent! I've generated eGatepass GP1719876543 for container ABCD1234567. The gatepass is valid for 48 hours and has been sent to ABC Logistics. Please ensure the truck driver has the reference number when arriving at the gate."

SYSTEM KNOWLEDGE:
- ETP: Electronic Terminal Portal (primary customer interface)
- OPUS/MGT: Container management and tracking system  
- CBAS: Vessel scheduling system
- WSS: Westports Security System (port pass management)
- SCSS: Smart Card Security System
- YPN: Yard Planning Navigator

CONTAINER STATUSES:
- ARRIVED: Container discharged from vessel
- DISCHARGED: Available in yard
- AVAILABLE_FOR_DELIVERY: Ready for pickup
- GATED_OUT: Exited terminal
- CUSTOMS_HOLD: Pending customs clearance
- DAMAGED: Requires inspection/repair

GREETING: "Hello, this is Aisha from Westports Document Center. I have live access to all our terminal systems and can assist you with real-time container inquiries, status updates, and documentation. How may I help you today?"

Remember: You are a LIVE system agent with real database access. Always use your tools to provide current, accurate information!
`;

// Get backend URL from environment or use localhost for demo
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

const ULTRAVOX_CALL_CONFIG = {
    systemPrompt: WESTPORTS_SYSTEM_PROMPT,
    model: 'fixie-ai/ultravox',
    voice: '87edb04c-06d4-47c2-bd94-683bc47e8fbe',
    temperature: 0.3,
    firstSpeaker: 'FIRST_SPEAKER_USER',
    medium: { "twilio": {} },
    selectedTools: [
        {
            temporaryTool: {
                name: "getContainerStatus",
                description: "Retrieve current container status, location, and details from ETP/OPUS system",
                definition: {
                    description: "Fetches real-time container information including status, location, vessel details, and charges",
                    dynamicParameters: [
                        {
                            name: "containerNumber",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Container number in format ABCD1234567",
                                pattern: "^[A-Z]{4}[0-9]{7}$"
                            },
                            required: true
                        }
                    ],
                    http: {
                        baseUrlPattern: `${BACKEND_URL}/api/containers/status`,
                        httpMethod: "POST"
                    }
                }
            }
        },
        {
            temporaryTool: {
                name: "updateContainerStatus",
                description: "Update container status in ETP/OPUS system with proper validation",
                definition: {
                    description: "Updates container status and triggers system-wide notifications",
                    dynamicParameters: [
                        {
                            name: "containerNumber",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Container number to update"
                            },
                            required: true
                        },
                        {
                            name: "newStatus",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "New container status",
                                enum: ["ARRIVED", "DISCHARGED", "GATED_OUT", "AVAILABLE_FOR_DELIVERY", "CUSTOMS_HOLD", "DAMAGED"]
                            },
                            required: true
                        },
                        {
                            name: "location",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Container location in terminal (e.g., Block A-15)"
                            },
                            required: false
                        }
                    ],
                    http: {
                        baseUrlPattern: `${BACKEND_URL}/api/containers/update`,
                        httpMethod: "POST"
                    }
                }
            }
        },
        {
            temporaryTool: {
                name: "generateEGatepass",
                description: "Generate electronic gatepass for container pickup through ETP system",
                definition: {
                    description: "Creates eGatepass with validation checks for EDO, customs clearance, and container availability",
                    dynamicParameters: [
                        {
                            name: "containerNumber",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Container number for gatepass generation"
                            },
                            required: true
                        },
                        {
                            name: "haulierCompany",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Registered haulier company name"
                            },
                            required: true
                        },
                        {
                            name: "truckNumber",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Truck registration number"
                            },
                            required: true
                        }
                    ],
                    http: {
                        baseUrlPattern: `${BACKEND_URL}/api/gatepass/generate`,
                        httpMethod: "POST"
                    }
                }
            }
        },
        {
            temporaryTool: {
                name: "checkVesselSchedule",
                description: "Check vessel arrival/departure schedule through CBAS system",
                definition: {
                    description: "Retrieves vessel schedule information including ETA, ETD, and berth allocation",
                    dynamicParameters: [
                        {
                            name: "vesselName",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Vessel name or IMO number"
                            },
                            required: false
                        },
                        {
                            name: "voyageNumber",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Voyage number"
                            },
                            required: false
                        }
                    ],
                    http: {
                        baseUrlPattern: `${BACKEND_URL}/api/vessels/schedule`,
                        httpMethod: "POST"
                    }
                }
            }
        },
        {
            temporaryTool: {
                name: "submitSSR",
                description: "Submit Special Service Request through ETP system",
                definition: {
                    description: "Creates SSR for various services like ITT, storage extension, or special handling",
                    dynamicParameters: [
                        {
                            name: "containerNumber",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Container number for SSR"
                            },
                            required: true
                        },
                        {
                            name: "ssrType",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Type of special service request",
                                enum: ["ITT", "STORAGE_EXTENSION", "REEFER_MONITORING", "SPECIAL_HANDLING", "GOVERNMENT_INSPECTION"]
                            },
                            required: true
                        },
                        {
                            name: "requestDetails",
                            location: "PARAMETER_LOCATION_BODY",
                            schema: {
                                type: "string",
                                description: "Detailed description of the service request"
                            },
                            required: true
                        }
                    ],
                    http: {
                        baseUrlPattern: `${BACKEND_URL}/api/ssr/submit`,
                        httpMethod: "POST"
                    }
                }
            }
        }
    ]
};

module.exports = {
    ULTRAVOX_CALL_CONFIG,
    WESTPORTS_SYSTEM_PROMPT
};