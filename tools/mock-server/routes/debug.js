/**
 * Debug and Testing Routes
 * Endpoints for development and testing (should NOT exist in production)
 */

import express from "express";
import { db, stats, resetData } from "../database.js";
import { config } from "../config.js";

const router = express.Router();

/**
 * GET /debug/data
 * View all stored data
 */
router.get("/data", (req, res) => {
  res.json({
    users: Array.from(db.users.values()).map((u) => {
      const { password, ...userWithoutPassword } = u;
      return userWithoutPassword;
    }),
    trips: Array.from(db.trips.values()),
    incidents: Array.from(db.incidents.values()),
    videos: Array.from(db.videos.values()),
    counts: {
      users: db.users.size,
      trips: db.trips.size,
      incidents: db.incidents.size,
      videos: db.videos.size,
    },
  });
});

/**
 * POST /debug/reset
 * Reset all data to initial seed
 */
router.post("/reset", async (req, res) => {
  await resetData();

  res.json({
    message: "Data reset successfully",
    counts: {
      users: db.users.size,
      trips: db.trips.size,
      incidents: db.incidents.size,
      videos: db.videos.size,
    },
  });
});

/**
 * POST /debug/errors/enable
 * Enable error simulation
 */
router.post("/errors/enable", (req, res) => {
  const { errorRate } = req.body;

  config.enableErrorSimulation = true;

  if (errorRate !== undefined) {
    const rate = parseFloat(errorRate);
    if (rate >= 0 && rate <= 1) {
      config.errorRate = rate;
    }
  }

  res.json({
    message: "Error simulation enabled",
    errorRate: config.errorRate,
  });
});

/**
 * POST /debug/errors/disable
 * Disable error simulation
 */
router.post("/errors/disable", (req, res) => {
  config.enableErrorSimulation = false;

  res.json({
    message: "Error simulation disabled",
  });
});

/**
 * GET /debug/stats
 * Get API usage statistics
 */
router.get("/stats", (req, res) => {
  const uptime = Math.floor((Date.now() - stats.startTime) / 1000);

  res.json({
    stats: {
      uptime,
      uptimeHuman: `${Math.floor(uptime / 3600)}h ${Math.floor(
        (uptime % 3600) / 60
      )}m ${uptime % 60}s`,
      requests: stats.requests,
      errors: stats.errors,
      data: {
        users: db.users.size,
        trips: db.trips.size,
        incidents: db.incidents.size,
        videos: db.videos.size,
      },
    },
  });
});

/**
 * GET /debug/health
 * Health check endpoint
 */
router.get("/health", (req, res) => {
  const uptime = Math.floor((Date.now() - stats.startTime) / 1000);
  const memoryUsage = process.memoryUsage();

  res.json({
    status: "healthy",
    uptime,
    memory: {
      heapUsed: `${Math.floor(memoryUsage.heapUsed / 1024 / 1024)} MB`,
      heapTotal: `${Math.floor(memoryUsage.heapTotal / 1024 / 1024)} MB`,
      rss: `${Math.floor(memoryUsage.rss / 1024 / 1024)} MB`,
    },
    timestamp: new Date().toISOString(),
  });
});

export default router;
