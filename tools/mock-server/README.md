# SafeDrive AI Mock API Server

Mock API server implementing the SafeDrive AI OpenAPI specification for mobile development and testing.

## Features

- ✅ Complete implementation of all API endpoints
- ✅ Realistic mock data generation with Faker
- ✅ JWT authentication with token validation
- ✅ In-memory data persistence
- ✅ Configurable response delays (simulate network)
- ✅ Error simulation for testing error handling
- ✅ Request logging and debugging tools
- ✅ CORS enabled for React Native
- ✅ Video upload with file storage
- ✅ Pagination, filtering, and sorting

## Quick Start

```bash
# Navigate to mock server directory
cd tools/mock-server

# Install dependencies
npm install

# Copy environment file
copy .env.example .env

# Start server
npm start

# Or start with auto-reload (requires Node 18+)
npm run dev
```

Server runs on **http://localhost:3001**

## Default Credentials

```
Email: demo@safedrive.ai
Password: Demo123456!

Email: test@safedrive.ai
Password: Test123456!

Email: alen@safedrive.ai
Password: Alen123456!
```

## API Endpoints

### Authentication

**Register new user**

```bash
curl -X POST http://localhost:3001/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"user@example.com\", \"password\": \"Password123!\", \"firstName\": \"John\", \"lastName\": \"Doe\", \"phone\": \"+14165551234\"}"
```

**Login**

```bash
curl -X POST http://localhost:3001/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"demo@safedrive.ai\", \"password\": \"Demo123456!\"}"
```

**Get profile** (requires JWT)

```bash
curl -X GET http://localhost:3001/auth/profile ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Update profile**

```bash
curl -X PUT http://localhost:3001/auth/profile ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"firstName\": \"Jane\"}"
```

### Trips

**Start trip**

```bash
curl -X POST http://localhost:3001/trips/start ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"startLocation\": {\"lat\": 43.6532, \"lng\": -79.3832}}"
```

**Stop trip**

```bash
curl -X POST http://localhost:3001/trips/stop ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"tripId\": \"TRIP_ID\", \"endLocation\": {\"lat\": 43.6426, \"lng\": -79.3871}}"
```

**List trips**

```bash
curl -X GET "http://localhost:3001/trips?limit=10&offset=0&status=completed" ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get trip details**

```bash
curl -X GET http://localhost:3001/trips/TRIP_ID ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Incidents

**Create incident**

```bash
curl -X POST http://localhost:3001/incidents ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"tripId\": \"TRIP_ID\", \"type\": \"distraction\", \"severity\": \"medium\", \"timestamp\": \"2025-11-13T14:30:00Z\", \"location\": {\"lat\": 43.6532, \"lng\": -79.3832}, \"speed\": 65.5, \"details\": {\"reason\": \"phone\", \"duration\": 5.2}}"
```

**Get trip incidents**

```bash
curl -X GET http://localhost:3001/incidents/trip/TRIP_ID ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Videos

**Upload video**

```bash
curl -X POST http://localhost:3001/videos/upload ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN" ^
  -F "tripId=TRIP_ID" ^
  -F "file=@C:\path\to\video.mp4" ^
  -F "duration=300" ^
  -F "resolution=1920x1080" ^
  -F "fps=30"
```

**Get video metadata**

```bash
curl -X GET http://localhost:3001/videos/VIDEO_ID ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get video download URL**

```bash
curl -X GET http://localhost:3001/videos/VIDEO_ID/download ^
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Debug Endpoints

**View all data**

```bash
curl -X GET http://localhost:3001/debug/data
```

**Reset data**

```bash
curl -X POST http://localhost:3001/debug/reset
```

**Enable error simulation** (10% error rate)

```bash
curl -X POST http://localhost:3001/debug/errors/enable ^
  -H "Content-Type: application/json" ^
  -d "{\"errorRate\": 0.1}"
```

**Disable error simulation**

```bash
curl -X POST http://localhost:3001/debug/errors/disable
```

**Get API stats**

```bash
curl -X GET http://localhost:3001/debug/stats
```

**Health check**

```bash
curl -X GET http://localhost:3001/debug/health
```

## Configuration

Edit `.env` file to customize behavior:

```env
# Server Configuration
PORT=3001

# JWT Configuration
JWT_SECRET=dev-secret-key-change-in-production
JWT_EXPIRY=24h

# Network Simulation
RESPONSE_DELAY_MS=100          # Add latency to simulate real network

# Error Simulation
ENABLE_ERROR_SIMULATION=false  # Randomly return errors for testing
ERROR_RATE=0.1                 # Error rate (0.0-1.0)

# Logging
LOG_LEVEL=debug                # debug | info | warn | error

# CORS Configuration (comma-separated origins)
CORS_ORIGIN=http://localhost:8081,http://192.168.1.100:8081

# File Upload
MAX_VIDEO_SIZE_MB=100          # Maximum video upload size
```

## React Native Integration

Create an API client in your React Native app:

```javascript
// api-client.js
import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Use your computer's local IP for testing on physical devices
// Use localhost for emulator/simulator
const API_BASE_URL = "http://192.168.1.100:3001";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests
apiClient.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem("authToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem("authToken");
      // Navigate to login screen
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Usage Examples

```javascript
import apiClient from "./api-client";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Login
const login = async () => {
  try {
    const { data } = await apiClient.post("/auth/login", {
      email: "demo@safedrive.ai",
      password: "Demo123456!",
    });

    await AsyncStorage.setItem("authToken", data.token);
    console.log("Logged in as:", data.user.firstName);
  } catch (error) {
    console.error("Login failed:", error.response?.data);
  }
};

// Start trip
const startTrip = async (latitude, longitude) => {
  try {
    const { data } = await apiClient.post("/trips/start", {
      startLocation: { lat: latitude, lng: longitude },
    });

    console.log("Trip started:", data.trip.id);
    return data.trip;
  } catch (error) {
    console.error("Failed to start trip:", error.response?.data);
  }
};

// Create incident
const logIncident = async (tripId, type, location, speed) => {
  try {
    const { data } = await apiClient.post("/incidents", {
      tripId,
      type,
      severity: "medium",
      timestamp: new Date().toISOString(),
      location,
      speed,
      details: { reason: type === "distraction" ? "phone" : null },
    });

    console.log("Incident logged:", data.incident.id);
  } catch (error) {
    console.error("Failed to log incident:", error.response?.data);
  }
};
```

## Testing Error Handling

Enable error simulation to test how your app handles failures:

```bash
# Enable 20% error rate
curl -X POST http://localhost:3001/debug/errors/enable ^
  -H "Content-Type: application/json" ^
  -d "{\"errorRate\": 0.2}"

# Now 1 in 5 requests will randomly fail
# Test your retry logic, error messages, offline handling, etc.

# Disable when done
curl -X POST http://localhost:3001/debug/errors/disable
```

## Data Persistence

Data is stored in memory and persists while the server is running. To reset data:

```bash
npm run reset
# or
curl -X POST http://localhost:3001/debug/reset
```

## Troubleshooting

### CORS Issues

If you get CORS errors, add your development URL to `.env`:

```env
CORS_ORIGIN=http://localhost:8081,http://192.168.1.100:8081
```

### Port Already in Use

Change the port in `.env`:

```env
PORT=3002
```

### Token Expiration

Tokens expire after 24h by default. Adjust in `.env`:

```env
JWT_EXPIRY=72h  # 3 days
```

### Finding Your Local IP

**Windows:**

```bash
ipconfig
# Look for IPv4 Address under your active network adapter
```

**macOS/Linux:**

```bash
ifconfig
# or
ip addr show
```

Then use this IP in your React Native app: `http://YOUR_IP:3001`

## Differences from Production API

- ❌ No actual S3 uploads (files saved locally in `uploads/`)
- ❌ No actual video processing
- ❌ No database persistence (in-memory only)
- ❌ Simplified authentication (no password reset, email verification)
- ❌ Debug endpoints that won't exist in production
- ❌ No rate limiting enforcement
- ❌ No email/SMS notifications
- ⚠️ JWT secret is insecure (for development only)

## Next Steps

1. ✅ Install dependencies and start the server
2. ✅ Test endpoints with curl or Postman
3. ✅ Integrate with your React Native app
4. ✅ Test error handling with error simulation
5. ⏳ When backend is ready, switch `API_BASE_URL` to production

## File Structure

```
tools/mock-server/
├── server.js              # Main Express server
├── config.js              # Configuration loader
├── database.js            # In-memory database
├── package.json           # Dependencies
├── .env.example           # Example environment file
├── .env                   # Your environment file (create from example)
├── middleware/
│   ├── auth.js           # JWT authentication
│   ├── delay.js          # Network latency simulation
│   ├── errorSimulation.js # Random error injection
│   └── errorHandler.js   # Global error handling
├── routes/
│   ├── auth.js           # Authentication endpoints
│   ├── trips.js          # Trip management
│   ├── incidents.js      # Incident logging
│   ├── videos.js         # Video upload
│   └── debug.js          # Debug/testing endpoints
├── uploads/               # Video file storage (created on first upload)
└── README.md             # This file
```

## Support

For issues or questions:

- Check the [main project README](../../README.md)
- Review [API specification](../../docs/api/openapi.yaml)
- Contact the SafeDrive AI team

---

**Built with ❤️ by the SafeDrive AI Team**
