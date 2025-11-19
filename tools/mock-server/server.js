/**
 * SafeDrive AI Mock API Server
 * Complete implementation of API endpoints for mobile development and testing
 */

import express from "express";
import cors from "cors";
import morgan from "morgan";
import { v4 as uuidv4 } from "uuid";
import { config } from "./config.js";
import { seedData, stats } from "./database.js";
import { delayMiddleware } from "./middleware/delay.js";
import { errorSimulationMiddleware } from "./middleware/errorSimulation.js";
import { errorHandler } from "./middleware/errorHandler.js";

// Import routes
import authRoutes from "./routes/auth.js";
import tripRoutes from "./routes/trips.js";
import incidentRoutes from "./routes/incidents.js";
import videoRoutes from "./routes/videos.js";
import debugRoutes from "./routes/debug.js";

const app = express();

// =============================================================================
// MIDDLEWARE SETUP
// =============================================================================

// CORS configuration
app.use(
  cors({
    origin: config.corsOrigin,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// Request logging
const morganFormat = config.logLevel === "debug" ? "dev" : "combined";
app.use(morgan(morganFormat));

// Body parsing
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Request ID middleware
app.use((req, res, next) => {
  req.id = uuidv4();
  res.setHeader("X-Request-ID", req.id);
  next();
});

// Response time tracking
app.use((req, res, next) => {
  const startTime = Date.now();

  res.on("finish", () => {
    const duration = Date.now() - startTime;

    // Track request stats
    const key = `${req.method} ${req.path}`;
    if (!stats.requests[key]) {
      stats.requests[key] = { count: 0, totalTime: 0 };
    }
    stats.requests[key].count++;
    stats.requests[key].totalTime += duration;

    if (config.logLevel === "debug") {
      console.log(`⏱️  ${req.method} ${req.path} completed in ${duration}ms`);
    }
  });

  next();
});

// Network delay simulation
app.use(delayMiddleware);

// Error simulation (if enabled)
app.use(errorSimulationMiddleware);

// =============================================================================
// ROUTES
// =============================================================================

/**
 * GET /
 * API information and documentation
 */
app.get("/", (req, res) => {
  res.json({
    name: "SafeDrive AI Mock API Server",
    version: "1.0.0",
    description: "Mock API server for mobile development and testing",
    documentation:
      "https://github.com/not0aag/SheridanCapstone2026/blob/main/tools/mock-server/README.md",
    endpoints: {
      auth: {
        register: "POST /auth/register",
        login: "POST /auth/login",
        profile: "GET /auth/profile (authenticated)",
      },
      trips: {
        start: "POST /trips/start (authenticated)",
        stop: "POST /trips/stop (authenticated)",
        list: "GET /trips (authenticated)",
        details: "GET /trips/:id (authenticated)",
      },
      incidents: {
        create: "POST /incidents (authenticated)",
        listByTrip: "GET /incidents/trip/:tripId (authenticated)",
      },
      videos: {
        upload: "POST /videos/upload (authenticated)",
        metadata: "GET /videos/:id (authenticated)",
        download: "GET /videos/:id/download (authenticated)",
      },
      debug: {
        data: "GET /debug/data",
        reset: "POST /debug/reset",
        health: "GET /debug/health",
        stats: "GET /debug/stats",
        enableErrors: "POST /debug/errors/enable",
        disableErrors: "POST /debug/errors/disable",
      },
    },
    demoCredentials: [
      { email: "demo@safedrive.ai", password: "Demo123456!" },
      { email: "test@safedrive.ai", password: "Test123456!" },
    ],
    config: {
      port: config.port,
      responseDelay: `${config.responseDelay}ms`,
      errorSimulation: config.enableErrorSimulation
        ? `enabled (${config.errorRate * 100}% rate)`
        : "disabled",
    },
  });
});

/**
 * GET /health
 * Health check endpoint (public)
 */
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    timestamp: new Date().toISOString(),
  });
});

// Mount API routes
app.use("/auth", authRoutes);
app.use("/trips", tripRoutes);
app.use("/incidents", incidentRoutes);
app.use("/videos", videoRoutes);
app.use("/debug", debugRoutes);

// =============================================================================
// ERROR HANDLING
// =============================================================================

// 404 handler for unknown routes
app.use((req, res) => {
  res.status(404).json({
    error: "Not Found",
    message: `Cannot ${req.method} ${req.path}`,
    statusCode: 404,
    timestamp: new Date().toISOString(),
    requestId: req.id,
  });
});

// Global error handler
app.use(errorHandler);

// =============================================================================
// SERVER STARTUP
// =============================================================================

async function startServer() {
  try {
    // Seed database with demo data
    await seedData();

    // Start server
    app.listen(config.port, () => {
      console.log("\n" + "=".repeat(60));
      console.log("🚀 SafeDrive AI Mock API Server");
      console.log("=".repeat(60));
      console.log(`\n📍 Server running on http://localhost:${config.port}`);
      console.log(`📚 API Documentation: http://localhost:${config.port}/`);
      console.log(`💊 Health Check: http://localhost:${config.port}/health`);
      console.log(`🔍 Debug Data: http://localhost:${config.port}/debug/data`);
      console.log("\n🔑 Demo Credentials:");
      console.log("   Email: demo@safedrive.ai");
      console.log("   Password: Demo123456!");
      console.log("\n⚙️  Configuration:");
      console.log(`   Response Delay: ${config.responseDelay}ms`);
      console.log(
        `   Error Simulation: ${
          config.enableErrorSimulation ? "ENABLED" : "disabled"
        }`
      );
      if (config.enableErrorSimulation) {
        console.log(`   Error Rate: ${(config.errorRate * 100).toFixed(1)}%`);
      }
      console.log("\n" + "=".repeat(60) + "\n");
    });
  } catch (error) {
    console.error("❌ Failed to start server:", error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on("SIGINT", () => {
  console.log("\n\n👋 Shutting down gracefully...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\n\n👋 Shutting down gracefully...");
  process.exit(0);
});

// Start the server
startServer();
