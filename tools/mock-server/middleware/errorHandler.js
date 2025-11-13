/**
 * Global Error Handler Middleware
 * Catches all errors and formats consistent error responses
 */

/**
 * Express error handling middleware
 * Must have 4 parameters (err, req, res, next) to be recognized as error handler
 */
export function errorHandler(err, req, res, next) {
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';
  
  // Log error with stack trace
  console.error(`[ERROR] ${req.id || 'unknown'}:`, {
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method
  });
  
  // Send formatted error response
  res.status(statusCode).json({
    error: err.name || 'Error',
    message,
    statusCode,
    timestamp: new Date().toISOString(),
    requestId: req.id || null,
    path: req.path
  });
}
