const twilio = require('twilio');
const https = require('https');
const { ULTRAVOX_CALL_CONFIG } = require('./ultravox_config');

// Configuration with provided credentials
const CONFIG = {
    twilio: {
        accountSid: 'ACa1e5c1c73ffa3ed3b6560ae7f0e1a413',
        authToken: 'ef4ab3a2b146100219c4a339750aac3b',
        phoneNumber: '+15076691592',
        destinationNumber: '+917981040722' // Demo number provided
    },
    ultravox: {
        apiKey: 'NbrolDNo.IzQOz3BA5QdtuvfsfNYBCYdv3BwULk11',
        apiUrl: 'https://api.ultravox.ai/api/calls'
    }
};

/**
 * Creates an Ultravox call with Westports-specific configuration
 * @returns {Promise}
 */
async function createUltravoxCall() {
    const request = https.request(CONFIG.ultravox.apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': CONFIG.ultravox.apiKey
        }
    });

    return new Promise((resolve, reject) => {
        let data = '';

        request.on('response', (response) => {
            response.on('data', chunk => data += chunk);
            response.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    if (result.joinUrl) {
                        resolve(result);
                    } else {
                        reject(new Error('No joinUrl in response: ' + data));
                    }
                } catch (error) {
                    reject(new Error('Invalid JSON response: ' + data));
                }
            });
        });

        request.on('error', reject);
        
        // Send the Ultravox configuration
        request.write(JSON.stringify(ULTRAVOX_CALL_CONFIG));
        request.end();
    });
}

/**
 * Main function to initiate the Westports demo call
 */
async function main() {
    try {
        console.log('🚀 Creating Westports Ultravox call...');
        console.log('📞 Destination:', CONFIG.twilio.destinationNumber);
        console.log('🎙️ AI Agent: Aisha (Westports Document Center)');
        console.log('📊 Dashboard: Monitor real-time updates at http://localhost:3000');
        
        const { joinUrl } = await createUltravoxCall();
        console.log('✅ Got joinUrl:', joinUrl);

        const client = twilio(CONFIG.twilio.accountSid, CONFIG.twilio.authToken);
        const call = await client.calls.create({
            twiml: `<Response><Connect><Stream url="${joinUrl}"/></Connect></Response>`,
            to: CONFIG.twilio.destinationNumber,
            from: CONFIG.twilio.phoneNumber
        });

        console.log('📱 Call initiated successfully!');
        console.log('📋 Call SID:', call.sid);
        console.log('🎯 Aisha is now ready to assist with Westports inquiries');
        console.log('');
        console.log('🗣️  Try these voice commands:');
        console.log('   "What\'s the status of container ABCD1234567?"');
        console.log('   "Update container EFGH9876543 to available for delivery"');
        console.log('   "Generate an eGatepass for container ABCD1234567 for ABC Logistics with truck WBE1234A"');
        console.log('   "Check the schedule for vessel MSC MAYA"');
        console.log('   "Submit an ITT request for container MSKU7654321"');
        console.log('');
        console.log('📊 Watch live updates at: http://localhost:3000');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.error('🔧 Please check your configuration and try again');
        
        // Additional debugging information
        if (error.message.includes('No joinUrl')) {
            console.error('💡 This might be an Ultravox API issue. Check your API key and configuration.');
        }
        if (error.message.includes('Invalid JSON')) {
            console.error('💡 The Ultravox API returned an invalid response. Check the API endpoint.');
        }
    }
}

// Execute the main function if this file is run directly
if (require.main === module) {
    main();
}

module.exports = { main, createUltravoxCall };