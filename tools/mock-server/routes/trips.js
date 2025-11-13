/**
 * Trip Management Routes
 * Handles trip lifecycle: start, stop, list, and details
 */

import express from 'express';
import { body, query, validationResult } from 'express-validator';
import { create, read, update, list } from '../database.js';
import { authMiddleware } from '../middleware/auth.js';

const router = express.Router();

// All trip routes require authentication
router.use(authMiddleware);

/**
 * POST /trips/start
 * Start a new trip
 */
router.post('/start',
  body('startLocation').isObject().withMessage('Start location is required'),
  body('startLocation.lat').isFloat({ min: -90, max: 90 }).withMessage('Valid latitude required'),
  body('startLocation.lng').isFloat({ min: -180, max: 180 }).withMessage('Valid longitude required'),
  body('timestamp').optional().isISO8601(),
  
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        errors: errors.array()
      });
    }
    
    // Check if user already has an active trip
    const activeTrips = list('trips', trip =>
      trip.userId === req.user.id && trip.status === 'active'
    );
    
    if (activeTrips.length > 0) {
      return res.status(400).json({
        error: 'Active trip already exists',
        message: 'Please stop your current trip before starting a new one',
        activeTripId: activeTrips[0].id
      });
    }
    
    const { startLocation, timestamp } = req.body;
    
    // Create new trip
    const trip = create('trips', {
      userId: req.user.id,
      startTime: timestamp || new Date().toISOString(),
      endTime: null,
      duration: null,
      distance: null,
      averageSpeed: null,
      maxSpeed: null,
      startLocation,
      endLocation: null,
      status: 'active',
      videoId: null,
      incidentCount: 0,
      distractionCount: 0,
      drowsinessCount: 0,
      crashDetected: false
    });
    
    res.status(201).json({
      trip
    });
  }
);

/**
 * POST /trips/stop
 * Stop an active trip
 */
router.post('/stop',
  body('tripId').notEmpty().withMessage('Trip ID is required'),
  body('endLocation').isObject().withMessage('End location is required'),
  body('endLocation.lat').isFloat({ min: -90, max: 90 }),
  body('endLocation.lng').isFloat({ min: -180, max: 180 }),
  body('timestamp').optional().isISO8601(),
  
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        errors: errors.array()
      });
    }
    
    const { tripId, endLocation, timestamp } = req.body;
    
    // Find trip
    const trip = read('trips', tripId);
    
    if (!trip) {
      return res.status(404).json({
        error: 'Trip not found'
      });
    }
    
    // Verify trip belongs to user
    if (trip.userId !== req.user.id) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'You can only stop your own trips'
      });
    }
    
    // Verify trip is active
    if (trip.status !== 'active') {
      return res.status(400).json({
        error: 'Trip is not active',
        message: `Trip status is '${trip.status}', cannot stop`
      });
    }
    
    // Calculate duration
    const endTime = timestamp || new Date().toISOString();
    const duration = Math.floor((new Date(endTime) - new Date(trip.startTime)) / 1000);
    
    // Calculate distance (simplified: straight line distance in meters)
    const R = 6371000; // Earth radius in meters
    const lat1 = trip.startLocation.lat * Math.PI / 180;
    const lat2 = endLocation.lat * Math.PI / 180;
    const deltaLat = (endLocation.lat - trip.startLocation.lat) * Math.PI / 180;
    const deltaLng = (endLocation.lng - trip.startLocation.lng) * Math.PI / 180;
    
    const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = Math.floor(R * c);
    
    // Calculate speeds
    const averageSpeed = distance > 0 ? Math.floor((distance / duration) * 3.6) : 0; // m/s to km/h
    const maxSpeed = averageSpeed > 0 ? Math.floor(averageSpeed * (1.2 + Math.random() * 0.3)) : 0;
    
    // Update trip
    const updatedTrip = update('trips', tripId, {
      status: 'completed',
      endTime,
      endLocation,
      duration,
      distance,
      averageSpeed,
      maxSpeed
    });
    
    res.json({
      trip: updatedTrip
    });
  }
);

/**
 * GET /trips
 * List user's trips with pagination and filtering
 */
router.get('/',
  query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
  query('offset').optional().isInt({ min: 0 }).toInt(),
  query('status').optional().isIn(['active', 'completed', 'cancelled']),
  query('startDate').optional().isISO8601(),
  query('endDate').optional().isISO8601(),
  query('sortBy').optional().isString(),
  query('sortOrder').optional().isIn(['asc', 'desc']),
  
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        errors: errors.array()
      });
    }
    
    const {
      limit = 20,
      offset = 0,
      status,
      startDate,
      endDate,
      sortBy = 'startTime',
      sortOrder = 'desc'
    } = req.query;
    
    // Get user's trips
    let trips = list('trips', trip => trip.userId === req.user.id);
    
    // Filter by status
    if (status) {
      trips = trips.filter(trip => trip.status === status);
    }
    
    // Filter by date range
    if (startDate) {
      trips = trips.filter(trip => new Date(trip.startTime) >= new Date(startDate));
    }
    if (endDate) {
      trips = trips.filter(trip => new Date(trip.startTime) <= new Date(endDate));
    }
    
    // Sort
    trips.sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    
    // Pagination
    const total = trips.length;
    const paginatedTrips = trips.slice(offset, offset + limit);
    
    res.json({
      trips: paginatedTrips,
      total,
      limit,
      offset,
      hasMore: offset + limit < total
    });
  }
);

/**
 * GET /trips/:id
 * Get trip details with incidents and video
 */
router.get('/:id', (req, res) => {
  const { id } = req.params;
  
  // Find trip
  const trip = read('trips', id);
  
  if (!trip) {
    return res.status(404).json({
      error: 'Trip not found'
    });
  }
  
  // Verify trip belongs to user
  if (trip.userId !== req.user.id) {
    return res.status(403).json({
      error: 'Forbidden',
      message: 'You can only view your own trips'
    });
  }
  
  // Get associated incidents
  const incidents = list('incidents', incident => incident.tripId === id);
  
  // Get associated video
  const video = trip.videoId ? read('videos', trip.videoId) : null;
  
  res.json({
    trip,
    incidents,
    video
  });
});

export default router;
