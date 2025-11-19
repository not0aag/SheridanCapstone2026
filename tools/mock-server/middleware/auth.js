/**
 * JWT Authentication Middleware
 * Handles token generation, validation, and user authentication
 */

import jwt from "jsonwebtoken";
import { config } from "../config.js";
import { db } from "../database.js";

/**
 * Generate JWT token for user
 * @param {string} userId - User ID
 * @param {string} email - User email
 * @returns {string} JWT token
 */
export function generateToken(userId, email) {
  const payload = {
    userId,
    email,
    iat: Math.floor(Date.now() / 1000),
  };

  return jwt.sign(payload, config.jwtSecret, {
    expiresIn: config.jwtExpiry,
  });
}

/**
 * Verify and decode JWT token
 * @param {string} token - JWT token
 * @returns {object|null} Decoded payload or null if invalid
 */
export function verifyToken(token) {
  try {
    return jwt.verify(token, config.jwtSecret);
  } catch (error) {
    if (error.name === "JsonWebTokenError") {
      return null;
    }
    if (error.name === "TokenExpiredError") {
      return null;
    }
    throw error;
  }
}

/**
 * Express middleware to authenticate requests
 * Extracts JWT from Authorization header and validates it
 */
export function authMiddleware(req, res, next) {
  // Extract token from Authorization header
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "No token provided",
      message: "Authorization header with Bearer token is required",
    });
  }

  const token = authHeader.substring(7); // Remove 'Bearer ' prefix

  // Verify token
  const decoded = verifyToken(token);

  if (!decoded) {
    return res.status(401).json({
      error: "Invalid or expired token",
      message: "Please login again",
    });
  }

  // Find user
  const user = db.users.get(decoded.userId);

  if (!user) {
    return res.status(401).json({
      error: "User not found",
      message: "The user associated with this token no longer exists",
    });
  }

  // Attach user to request
  req.user = {
    id: user.id,
    email: user.email,
    firstName: user.firstName,
    lastName: user.lastName,
  };

  next();
}
