/**
 * Authentication Routes
 * Handles user registration, login, and profile management
 */

import express from "express";
import bcrypt from "bcrypt";
import { body, validationResult } from "express-validator";
import { create, read, update, list } from "../database.js";
import { generateToken, authMiddleware } from "../middleware/auth.js";

const router = express.Router();

/**
 * POST /auth/register
 * Register a new user
 */
router.post(
  "/register",
  // Validation
  body("email").isEmail().withMessage("Valid email is required"),
  body("password")
    .isLength({ min: 8 })
    .withMessage("Password must be at least 8 characters")
    .matches(/[A-Za-z]/)
    .withMessage("Password must contain a letter")
    .matches(/[0-9]/)
    .withMessage("Password must contain a number"),
  body("firstName").notEmpty().withMessage("First name is required"),
  body("lastName").notEmpty().withMessage("Last name is required"),
  body("phone").notEmpty().withMessage("Phone number is required"),

  async (req, res) => {
    // Check validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: "Validation failed",
        message: "Please check your input",
        errors: errors.array(),
      });
    }

    const { email, password, firstName, lastName, phone, emergencyContacts } =
      req.body;

    // Check if email already exists
    const existingUsers = list(
      "users",
      (user) => user.email === email.toLowerCase()
    );
    if (existingUsers.length > 0) {
      return res.status(400).json({
        error: "Email already registered",
        message: "A user with this email already exists",
      });
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);

    // Create user
    const user = create("users", {
      email: email.toLowerCase(),
      password: passwordHash,
      firstName,
      lastName,
      phone,
      emergencyContacts: emergencyContacts || [],
    });

    // Generate token
    const token = generateToken(user.id, user.email);

    // Return user without password
    const { password: _, ...userWithoutPassword } = user;

    res.status(201).json({
      user: userWithoutPassword,
      token,
    });
  }
);

/**
 * POST /auth/login
 * Authenticate user and return JWT token
 */
router.post(
  "/login",
  body("email").isEmail().withMessage("Valid email is required"),
  body("password").notEmpty().withMessage("Password is required"),

  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: "Validation failed",
        errors: errors.array(),
      });
    }

    const { email, password } = req.body;

    // Find user by email
    const users = list("users", (user) => user.email === email.toLowerCase());

    if (users.length === 0) {
      return res.status(401).json({
        error: "Invalid credentials",
        message: "Email or password is incorrect",
      });
    }

    const user = users[0];

    // Compare password
    const isValidPassword = await bcrypt.compare(password, user.password);

    if (!isValidPassword) {
      return res.status(401).json({
        error: "Invalid credentials",
        message: "Email or password is incorrect",
      });
    }

    // Generate token
    const token = generateToken(user.id, user.email);

    // Return user without password
    const { password: _, ...userWithoutPassword } = user;

    res.json({
      user: userWithoutPassword,
      token,
    });
  }
);

/**
 * GET /auth/profile
 * Get current user profile (requires authentication)
 */
router.get("/profile", authMiddleware, (req, res) => {
  const user = read("users", req.user.id);

  if (!user) {
    return res.status(404).json({
      error: "User not found",
    });
  }

  // Return user without password
  const { password, ...userWithoutPassword } = user;

  res.json({
    user: userWithoutPassword,
  });
});

/**
 * PUT /auth/profile
 * Update current user profile (requires authentication)
 */
router.put(
  "/profile",
  authMiddleware,
  body("firstName").optional().notEmpty(),
  body("lastName").optional().notEmpty(),
  body("phone").optional().notEmpty(),

  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: "Validation failed",
        errors: errors.array(),
      });
    }

    const { firstName, lastName, phone, emergencyContacts } = req.body;

    // Build update object
    const updates = {};
    if (firstName) updates.firstName = firstName;
    if (lastName) updates.lastName = lastName;
    if (phone) updates.phone = phone;
    if (emergencyContacts) updates.emergencyContacts = emergencyContacts;

    // Update user
    const updatedUser = update("users", req.user.id, updates);

    if (!updatedUser) {
      return res.status(404).json({
        error: "User not found",
      });
    }

    // Return user without password
    const { password, ...userWithoutPassword } = updatedUser;

    res.json({
      user: userWithoutPassword,
    });
  }
);

export default router;
