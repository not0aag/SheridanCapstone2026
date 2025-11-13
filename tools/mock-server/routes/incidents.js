/**
 * Incident Logging Routes
 * Handles incident creation and retrieval
 */

import express from 'express';
import { body, query, validationResult } from 'express-validator';
import { create, read, update, list } from '../database.js';
import { authMiddleware } from '../middleware/auth.js';

const router = express.Router();

// All incident routes require authentication
router.use(authMiddleware);

/**
 * POST /incidents
 * Create a new incident
 */
router.post('/',
  body('tripId').notEmpty().withMessage('Trip ID is required'),
  body('type').isIn(['distraction', 'drowsiness', 'crash', 'speeding']).withMessage('Valid type required'),
  body('severity').isIn(['low', 'medium', 'high', 'critical']).withMessage('Valid severity required'),
  body('timestamp').isISO8601().withMessage('Valid timestamp required'),
  body('location').isObject().withMessage('Location is required'),
  body('location.lat').isFloat({ min: -90, max: 90 }),
  body('location.lng').isFloat({ min: -180, max: 180 }),
  body('speed').isFloat({ min: 0 }).withMessage('Valid speed required'),
  body('details').optional().isObject(),
  body('videoTimestamp').optional().isFloat({ min: 0 }),
  
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        errors: errors.array()
      });
    }
    
    const {
      tripId,
      type,
      severity,
      timestamp,
      location,
      speed,
      details,
      videoTimestamp
    } = req.body;
    
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
        message: 'You can only create incidents for your own trips'
      });
    }
    
    // Verify timestamp is within trip duration
    if (trip.endTime && new Date(timestamp) > new Date(trip.endTime)) {
      return res.status(400).json({
        error: 'Invalid timestamp',
        message: 'Incident timestamp is after trip end time'
      });
    }
    
    if (new Date(timestamp) < new Date(trip.startTime)) {
      return res.status(400).json({
        error: 'Invalid timestamp',
        message: 'Incident timestamp is before trip start time'
      });
    }
    
    // Create incident
    const incident = create('incidents', {
      tripId,
      userId: req.user.id,
      type,
      severity,
      timestamp,
      location,
      speed,
      details: details || {},
      videoTimestamp: videoTimestamp || null,
      resolved: false
    });
    
    // Update trip incident counters
    const updates = {
      incidentCount: trip.incidentCount + 1
    };
    
    if (type === 'distraction') {
      updates.distractionCount = trip.distractionCount + 1;
    } else if (type === 'drowsiness') {
      updates.drowsinessCount = trip.drowsinessCount + 1;
    } else if (type === 'crash') {
      updates.crashDetected = true;
    }
    
    update('trips', tripId, updates);
    
    res.status(201).json({
      incident
    });
  }
);

/**
 * GET /incidents/trip/:tripId
 * Get all incidents for a trip
 */
router.get('/trip/:tripId',
  query('type').optional().isIn(['distraction', 'drowsiness', 'crash', 'speeding']),
  query('severity').optional().isIn(['low', 'medium', 'high', 'critical']),
  query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
  query('offset').optional().isInt({ min: 0 }).toInt(),
  
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        errors: errors.array()
      });
    }
    
    const { tripId } = req.params;
    const {
      type,
      severity,
      limit = 50,
      offset = 0
    } = req.query;
    
    // Verify trip exists and belongs to user
    const trip = read('trips', tripId);
    
    if (!trip) {
      return res.status(404).json({
        error: 'Trip not found'
      });
    }
    
    if (trip.userId !== req.user.id) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'You can only view incidents for your own trips'
      });
    }
    
    // Get incidents for trip
    let incidents = list('incidents', incident => incident.tripId === tripId);
    
    // Filter by type
    if (type) {
      incidents = incidents.filter(incident => incident.type === type);
    }
    
    // Filter by severity
    if (severity) {
      incidents = incidents.filter(incident => incident.severity === severity);
    }
    
    // Sort by timestamp descending (most recent first)
    incidents.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Pagination
    const total = incidents.length;
    const paginatedIncidents = incidents.slice(offset, offset + limit);
    
    res.json({
      incidents: paginatedIncidents,
      total,
      limit,
      offset
    });
  }
);

export default router;
