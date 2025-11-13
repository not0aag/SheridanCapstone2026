/**
 * Network Latency Simulation Middleware
 * Adds configurable delay to responses to simulate real network conditions
 */

import { config } from '../config.js';

/**
 * Add delay before processing request
 * Skips delay for health check and debug endpoints
 */
export function delayMiddleware(req, res, next) {
  // Skip delay for certain endpoints
  if (req.path.startsWith('/health') || req.path.startsWith('/debug')) {
    return next();
  }
  
  // Add jitter: ±50ms random variation
  const jitter = Math.random() * 100 - 50;
  const delay = Math.max(0, config.responseDelay + jitter);
  
  // Log delay if in debug mode
  if (config.logLevel === 'debug') {
    console.log(`⏱️  Adding ${delay.toFixed(0)}ms delay to ${req.method} ${req.path}`);
  }
  
  setTimeout(next, delay);
}
