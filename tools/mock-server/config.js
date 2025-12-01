/**
 * Configuration loader for SafeDrive Mock API Server
 * Loads environment variables and provides sensible defaults
 */

import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.join(__dirname, ".env") });

// Validate required environment variables
const requiredVars = [];
const missingVars = requiredVars.filter((v) => !process.env[v]);

if (missingVars.length > 0) {
  console.warn(`⚠️  Missing environment variables: ${missingVars.join(", ")}`);
  console.warn(
    "⚠️  Using default values. Copy .env.example to .env for production use."
  );
}

// Export configuration
export const config = {
  // Server
  port: parseInt(process.env.PORT) || 3001,

  // JWT
  jwtSecret: process.env.JWT_SECRET || "dev-secret-not-secure",
  jwtExpiry: process.env.JWT_EXPIRY || "24h",

  // Network simulation
  responseDelay: parseInt(process.env.RESPONSE_DELAY_MS) || 100,

  // Error simulation
  enableErrorSimulation: process.env.ENABLE_ERROR_SIMULATION === "true",
  errorRate: parseFloat(process.env.ERROR_RATE) || 0.1,

  // Logging
  logLevel: process.env.LOG_LEVEL || "info",

  // CORS
  corsOrigin: process.env.CORS_ORIGIN?.split(",") || ["*"],

  // File upload
  maxVideoSize: (parseInt(process.env.MAX_VIDEO_SIZE_MB) || 100) * 1024 * 1024,
  uploadDir: path.join(__dirname, "uploads"),
};

// Log configuration on startup (hide secrets)
const safeConfig = {
  ...config,
  jwtSecret:
    config.jwtSecret === "dev-secret-not-secure"
      ? "*** (default) ***"
      : "*** (custom) ***",
};

console.log("📝 Configuration loaded:", safeConfig);
