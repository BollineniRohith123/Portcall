import React, { useState, useEffect } from 'react';

const WestportsVoiceDashboard = () => {
    const [dashboardData, setDashboardData] = useState({
        containers: [],
        vessels: [],
        gatepasses: [],
        ssrRequests: []
    });
    const [recentActivities, setRecentActivities] = useState([]);
    const [socket, setSocket] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('Connecting...');

    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

    useEffect(() => {
        // Initialize WebSocket connection
        const wsUrl = backendUrl.replace('http', 'ws') + '/ws';
        const newSocket = new WebSocket(wsUrl);
        setSocket(newSocket);

        newSocket.onopen = () => {
            setConnectionStatus('Connected');
            console.log('Connected to Westports backend');
        };

        newSocket.onclose = () => {
            setConnectionStatus('Disconnected');
        };

        newSocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnectionStatus('Error');
        };

        // Fetch initial dashboard data
        fetchDashboardData();

        // Listen for real-time updates
        newSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleRealtimeUpdate(data);
        };

        return () => newSocket.close();
    }, [backendUrl]);

    const fetchDashboardData = async () => {
        try {
            const response = await fetch(`${backendUrl}/api/dashboard`);
            const result = await response.json();
            if (result.success) {
                setDashboardData(result.data);
            }
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        }
    };

    const handleRealtimeUpdate = (data) => {
        switch (data.type) {
            case 'containerQueried':
                addActivity(`🔍 Container ${data.containerNumber} queried via Aisha AI`, data.timestamp, 'query');
                highlightContainer(data.containerNumber);
                break;
            case 'containerUpdated':
                updateContainerInState(data.data);
                addActivity(`🔄 Container ${data.containerNumber} updated: ${data.oldStatus} → ${data.newStatus}`, data.timestamp, 'update');
                showNotification(`Container ${data.containerNumber} updated to ${data.newStatus}`, 'success');
                break;
            case 'gatepassGenerated':
                addGatepassToState(data.gatepass);
                addActivity(`📋 eGatepass ${data.gatepass.id} generated for ${data.containerNumber}`, data.timestamp, 'gatepass');
                showNotification(`eGatepass ${data.gatepass.id} generated successfully`, 'success');
                break;
            case 'vesselQueried':
                addActivity(`🚢 Vessel ${data.vesselName} schedule queried via Aisha AI`, data.timestamp, 'vessel');
                break;
            case 'ssrSubmitted':
                addSSRToState(data.ssr);
                addActivity(`📝 SSR ${data.ssr.id} submitted for ${data.containerNumber} (${data.ssr.ssrType})`, data.timestamp, 'ssr');
                showNotification(`SSR submitted successfully: ${data.ssr.id}`, 'info');
                break;
        }
    };

    const updateContainerInState = (updatedContainer) => {
        setDashboardData(prev => ({
            ...prev,
            containers: prev.containers.map(container =>
                container.containerNumber === updatedContainer.containerNumber
                    ? updatedContainer
                    : container
            )
        }));
    };

    const addGatepassToState = (newGatepass) => {
        setDashboardData(prev => ({
            ...prev,
            gatepasses: [...prev.gatepasses, newGatepass]
        }));
    };

    const addSSRToState = (newSSR) => {
        setDashboardData(prev => ({
            ...prev,
            ssrRequests: [...prev.ssrRequests, newSSR]
        }));
    };

    const addActivity = (message, timestamp, type) => {
        setRecentActivities(prev => [
            { 
                message, 
                timestamp, 
                type,
                id: Date.now() + Math.random()
            },
            ...prev.slice(0, 14) // Keep last 15 activities
        ]);
    };

    const highlightContainer = (containerNumber) => {
        const element = document.getElementById(`container-${containerNumber}`);
        if (element) {
            element.classList.add('highlight-query');
            setTimeout(() => {
                element.classList.remove('highlight-query');
            }, 4000);
        }
    };

    const showNotification = (message, type) => {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div>
                <strong>🎙️ Live Update!</strong><br/>
                ${message}
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    };

    const getStatusColor = (status) => {
        const colors = {
            'ARRIVED': 'bg-blue-500',
            'DISCHARGED': 'bg-yellow-500',
            'AVAILABLE_FOR_DELIVERY': 'bg-green-500',
            'GATED_OUT': 'bg-gray-500',
            'CUSTOMS_HOLD': 'bg-red-500',
            'DAMAGED': 'bg-orange-500'
        };
        return colors[status] || 'bg-gray-400';
    };

    const getActivityIcon = (type) => {
        const icons = {
            'query': '🔍',
            'update': '🔄',
            'gatepass': '📋',
            'vessel': '🚢',
            'ssr': '📝'
        };
        return icons[type] || '📊';
    };

    return (
        <div className="westports-dashboard">
            {/* Header */}
            <div className="header">
                <div className="demo-badge">
                    🎙️ Westports AI Voice Agent - Live Demo
                </div>
                <span className={`connection-status ${connectionStatus === 'Connected' ? 'connected' : 'disconnected'}`}>
                    ● {connectionStatus}
                </span>
                <h1>Westports Container Management System</h1>
                <p>Real-time voice AI integration with ETP, OPUS, CBAS, and WSS systems</p>
            </div>

            {/* Call Instructions */}
            <div className="call-instructions">
                <h2>📞 Experience Aisha - Your AI Westports Assistant</h2>
                <p>Call now to interact with our live AI agent:</p>
                <div className="phone-number">+1 (507) 669-1592</div>
                <p><strong>Try these voice commands:</strong></p>
                <div className="command-list">
                    <div>"What's the status of container ABCD1234567?"</div>
                    <div>"Update container EFGH9876543 to available for delivery"</div>
                    <div>"Generate an eGatepass for container ABCD1234567"</div>
                    <div>"Check the schedule for vessel MSC MAYA"</div>
                    <div>"Submit an ITT request for container MSKU7654321"</div>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-number">{dashboardData.containers.length}</div>
                    <div className="stat-label">Total Containers</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">
                        {dashboardData.containers.filter(c => c.availableForPickup).length}
                    </div>
                    <div className="stat-label">Available for Pickup</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">{dashboardData.gatepasses.length}</div>
                    <div className="stat-label">Active Gatepasses</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">{recentActivities.length}</div>
                    <div className="stat-label">Voice Interactions</div>
                </div>
            </div>

            {/* Main Dashboard Grid */}
            <div className="dashboard-grid">
                {/* Container Status Section */}
                <div className="section">
                    <h2>Container Status (Live ETP/OPUS Data)</h2>
                    {dashboardData.containers.length === 0 ? (
                        <div className="empty-state">Loading container data...</div>
                    ) : (
                        dashboardData.containers.map(container => (
                            <div 
                                key={container.containerNumber}
                                id={`container-${container.containerNumber}`}
                                className="container-card"
                            >
                                <div className="container-header">
                                    <div className="container-number">
                                        {container.containerNumber}
                                    </div>
                                    <div className={`status-badge ${getStatusColor(container.status)}`}>
                                        {container.status}
                                    </div>
                                </div>
                                <div className="container-details">
                                    <div className="detail-item">
                                        <span>Vessel:</span>
                                        <span>{container.vesselName}</span>
                                    </div>
                                    <div className="detail-item">
                                        <span>Location:</span>
                                        <span>{container.location}</span>
                                    </div>
                                    <div className="detail-item">
                                        <span>Type/Size:</span>
                                        <span>{container.containerType} {container.size}</span>
                                    </div>
                                    <div className="detail-item">
                                        <span>Charges:</span>
                                        <span>{container.currency} {container.charges}</span>
                                    </div>
                                    <div className="detail-item">
                                        <span>EDO Status:</span>
                                        <span className={container.edoStatus === 'RELEASED' ? 'text-green-600' : 'text-red-600'}>
                                            {container.edoStatus}
                                        </span>
                                    </div>
                                    <div className="detail-item">
                                        <span>Customs:</span>
                                        <span className={container.customsStatus === 'CLEARED' ? 'text-green-600' : 'text-red-600'}>
                                            {container.customsStatus}
                                        </span>
                                    </div>
                                </div>
                                {container.activeGatepass && (
                                    <div className="active-gatepass">
                                        🎫 Active Gatepass: {container.activeGatepass}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Live Activities Section */}
                <div className="section">
                    <h2>Live Voice Activities</h2>
                    {recentActivities.length === 0 ? (
                        <div className="empty-state">
                            No voice interactions yet.<br/>
                            Call +1 (507) 669-1592 to see live updates!
                        </div>
                    ) : (
                        recentActivities.map(activity => (
                            <div key={activity.id} className="activity-item">
                                <div className="activity-message">
                                    {getActivityIcon(activity.type)} {activity.message}
                                </div>
                                <div className="activity-time">
                                    {new Date(activity.timestamp).toLocaleString()}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Recent Gatepasses */}
            {dashboardData.gatepasses.length > 0 && (
                <div className="section">
                    <h2>Recent eGatepasses</h2>
                    {dashboardData.gatepasses.map(gatepass => (
                        <div key={gatepass.id} className="gatepass-card">
                            <div className="gatepass-id">{gatepass.id}</div>
                            <div className="gatepass-details">
                                Container: {gatepass.containerNumber} | 
                                Haulier: {gatepass.haulierCompany} | 
                                Valid until: {new Date(gatepass.validUntil).toLocaleString()}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Recent SSR Submissions */}
            {dashboardData.ssrRequests.length > 0 && (
                <div className="section">
                    <h2>Recent SSR Submissions</h2>
                    {dashboardData.ssrRequests.map(ssr => (
                        <div key={ssr.id} className="ssr-card">
                            <div className="ssr-id">{ssr.id} - {ssr.ssrType}</div>
                            <div className="ssr-details">
                                Container: {ssr.containerNumber} | 
                                Status: {ssr.status} | 
                                Submitted: {new Date(ssr.submittedAt).toLocaleString()}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default WestportsVoiceDashboard;