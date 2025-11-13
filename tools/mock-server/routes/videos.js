/**
 * Video Upload and Retrieval Routes
 * Handles video upload, metadata, and download
 */

import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { create, read, update } from '../database.js';
import { authMiddleware } from '../middleware/auth.js';
import { config } from '../config.js';

const router = express.Router();

// Ensure uploads directory exists
if (!fs.existsSync(config.uploadDir)) {
  fs.mkdirSync(config.uploadDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, config.uploadDir);
  },
  filename: (req, file, cb) => {
    const tripId = req.body.tripId || 'unknown';
    const timestamp = Date.now();
    const ext = path.extname(file.originalname);
    cb(null, `trip_${tripId}_${timestamp}${ext}`);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: config.maxVideoSize
  },
  fileFilter: (req, file, cb) => {
    // Accept only video files
    const allowedMimes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
    
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Only video files are allowed (MP4, MOV, AVI)'));
    }
  }
});

// All video routes require authentication
router.use(authMiddleware);

/**
 * POST /videos/upload
 * Upload a video file
 */
router.post('/upload',
  upload.single('file'),
  (req, res) => {
    if (!req.file) {
      return res.status(400).json({
        error: 'No file uploaded',
        message: 'Please provide a video file'
      });
    }
    
    const { tripId, duration, resolution, fps } = req.body;
    
    if (!tripId) {
      // Clean up uploaded file
      fs.unlinkSync(req.file.path);
      return res.status(400).json({
        error: 'Trip ID required',
        message: 'Please provide tripId in the request body'
      });
    }
    
    // Verify trip exists and belongs to user
    const trip = read('trips', tripId);
    
    if (!trip) {
      fs.unlinkSync(req.file.path);
      return res.status(404).json({
        error: 'Trip not found'
      });
    }
    
    if (trip.userId !== req.user.id) {
      fs.unlinkSync(req.file.path);
      return res.status(403).json({
        error: 'Forbidden',
        message: 'You can only upload videos for your own trips'
      });
    }
    
    // Create video record
    const video = create('videos', {
      tripId,
      userId: req.user.id,
      filename: req.file.filename,
      originalName: req.file.originalname,
      size: req.file.size,
      duration: duration ? parseFloat(duration) : null,
      format: path.extname(req.file.filename).substring(1).toUpperCase(),
      resolution: resolution || 'unknown',
      fps: fps ? parseInt(fps) : null,
      uploadedAt: new Date().toISOString(),
      url: `/uploads/${req.file.filename}`,
      path: req.file.path
    });
    
    // Update trip with video ID
    update('trips', tripId, { videoId: video.id });
    
    res.status(201).json({
      video: {
        id: video.id,
        tripId: video.tripId,
        filename: video.filename,
        size: video.size,
        duration: video.duration,
        format: video.format,
        resolution: video.resolution,
        fps: video.fps,
        uploadedAt: video.uploadedAt,
        url: video.url
      }
    });
  }
);

/**
 * GET /videos/:id
 * Get video metadata
 */
router.get('/:id', (req, res) => {
  const { id } = req.params;
  
  // Find video
  const video = read('videos', id);
  
  if (!video) {
    return res.status(404).json({
      error: 'Video not found'
    });
  }
  
  // Verify video belongs to user (via trip)
  const trip = read('trips', video.tripId);
  
  if (!trip || trip.userId !== req.user.id) {
    return res.status(403).json({
      error: 'Forbidden',
      message: 'You can only view your own videos'
    });
  }
  
  res.json({
    video: {
      id: video.id,
      tripId: video.tripId,
      filename: video.filename,
      size: video.size,
      duration: video.duration,
      format: video.format,
      resolution: video.resolution,
      fps: video.fps,
      uploadedAt: video.uploadedAt
    }
  });
});

/**
 * GET /videos/:id/download
 * Get pre-signed download URL (simulated)
 */
router.get('/:id/download', (req, res) => {
  const { id } = req.params;
  
  // Find video
  const video = read('videos', id);
  
  if (!video) {
    return res.status(404).json({
      error: 'Video not found'
    });
  }
  
  // Verify video belongs to user
  const trip = read('trips', video.tripId);
  
  if (!trip || trip.userId !== req.user.id) {
    return res.status(403).json({
      error: 'Forbidden',
      message: 'You can only download your own videos'
    });
  }
  
  // Generate mock pre-signed URL
  const expiresIn = 3600; // 1 hour
  const expiresAt = new Date(Date.now() + expiresIn * 1000).toISOString();
  
  res.json({
    url: `https://mock-s3.safedrive.ai/videos/${video.filename}?expires=${expiresAt}`,
    expiresIn,
    expiresAt
  });
});

export default router;
