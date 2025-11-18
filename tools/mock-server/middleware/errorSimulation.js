/**
 * Error Simulation Middleware
 * Randomly injects errors for testing error handling in clients
 */

import { config } from "../config.js";

/**
 * Randomly return errors based on configuration
 * Helps test error handling, retries, and resilience
 */
export function errorSimulationMiddleware(req, res, next) {
  // Skip if error simulation is disabled
  if (!config.enableErrorSimulation) {
    return next();
  }

  // Skip for authentication and debug endpoints
  if (
    req.path.startsWith("/auth") ||
    req.path.startsWith("/debug") ||
    req.path.startsWith("/health")
  ) {
    return next();
  }

  // Randomly inject error based on error rate
  const shouldError = Math.random() < config.errorRate;

  if (shouldError) {
    // Select random error type
    const errorTypes = [
      { status: 500, message: "Internal Server Error" },
      { status: 503, message: "Service Unavailable" },
      { status: 429, message: "Too Many Requests" },
      { status: 408, message: "Request Timeout" },
    ];

    const weights = [0.5, 0.25, 0.15, 0.1]; // Probability distribution
    let random = Math.random();
    let errorIndex = 0;

    for (let i = 0; i < weights.length; i++) {
      random -= weights[i];
      if (random <= 0) {
        errorIndex = i;
        break;
      }
    }

    const error = errorTypes[errorIndex];

    console.log(
      `❌ [ERROR SIMULATION] ${req.method} ${req.path} → ${error.status} ${error.message}`
    );

    return res.status(error.status).json({
      error: error.message,
      message: "This is a simulated error for testing purposes",
      statusCode: error.status,
      timestamp: new Date().toISOString(),
      path: req.path,
      simulated: true,
    });
  }

  next();
}
