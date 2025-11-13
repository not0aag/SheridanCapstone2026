/**
 * In-memory database for SafeDrive Mock API Server
 * Provides CRUD operations and data persistence during runtime
 */

import { faker } from '@faker-js/faker';
import bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';

// Data stores
export const db = {
  users: new Map(),
  trips: new Map(),
  incidents: new Map(),
  videos: new Map(),
  sessions: new Map()
};

// Statistics tracking
export const stats = {
  requests: {},
  errors: 0,
  startTime: Date.now()
};

/**
 * CRUD Operations
 */

export function create(collection, data) {
  const id = data.id || uuidv4();
  const timestamp = new Date().toISOString();
  
  const record = {
    ...data,
    id,
    createdAt: data.createdAt || timestamp,
    updatedAt: timestamp
  };
  
  db[collection].set(id, record);
  return record;
}

export function read(collection, id) {
  return db[collection].get(id) || null;
}

export function update(collection, id, data) {
  const existing = db[collection].get(id);
  if (!existing) return null;
  
  const updated = {
    ...existing,
    ...data,
    id, // Preserve ID
    createdAt: existing.createdAt, // Preserve creation time
    updatedAt: new Date().toISOString()
  };
  
  db[collection].set(id, updated);
  return updated;
}

export function deleteRecord(collection, id) {
  return db[collection].delete(id);
}

export function list(collection, filter = () => true) {
  const records = Array.from(db[collection].values());
  return records.filter(filter);
}

export function search(collection, query) {
  const records = Array.from(db[collection].values());
  const queryLower = query.toLowerCase();
  
  return records.filter(record => {
    const searchableText = JSON.stringify(record).toLowerCase();
    return searchableText.includes(queryLower);
  });
}

/**
 * Seed demo data
 */

export async function seedData() {
  console.log('🌱 Seeding database with demo data...');
  
  // Create demo users
  const demoUsers = [
    {
      email: 'demo@safedrive.ai',
      password: await bcrypt.hash('Demo123456!', 10),
      firstName: 'Demo',
      lastName: 'User',
      phone: '+14165551234',
      emergencyContacts: [
        { name: 'Jane Doe', phone: '+14165555678', relationship: 'Spouse' }
      ]
    },
    {
      email: 'test@safedrive.ai',
      password: await bcrypt.hash('Test123456!', 10),
      firstName: 'Test',
      lastName: 'User',
      phone: '+14165559999',
      emergencyContacts: [
        { name: 'John Smith', phone: '+14165554321', relationship: 'Parent' }
      ]
    },
    {
      email: 'alen@safedrive.ai',
      password: await bcrypt.hash('Alen123456!', 10),
      firstName: 'Alen',
      lastName: 'George',
      phone: '+14165553000',
      emergencyContacts: []
    }
  ];
  
  for (const userData of demoUsers) {
    create('users', userData);
  }
  
  // Create sample trips
  const users = Array.from(db.users.values());
  const tripStatuses = ['completed', 'completed', 'completed', 'completed', 'completed', 'active', 'active'];
  
  for (let i = 0; i < 10; i++) {
    const user = users[i % users.length];
    const status = tripStatuses[i % tripStatuses.length];
    const startTime = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000);
    const duration = Math.floor(Math.random() * 3600) + 600; // 10-70 minutes
    const endTime = status === 'completed' ? new Date(startTime.getTime() + duration * 1000) : null;
    
    const trip = create('trips', {
      userId: user.id,
      startTime: startTime.toISOString(),
      endTime: endTime?.toISOString() || null,
      duration: status === 'completed' ? duration : null,
      distance: status === 'completed' ? Math.floor(Math.random() * 50000) + 5000 : null,
      averageSpeed: status === 'completed' ? Math.floor(Math.random() * 50) + 40 : null,
      maxSpeed: status === 'completed' ? Math.floor(Math.random() * 40) + 80 : null,
      startLocation: {
        lat: 43.6532 + (Math.random() - 0.5) * 0.1,
        lng: -79.3832 + (Math.random() - 0.5) * 0.1
      },
      endLocation: status === 'completed' ? {
        lat: 43.6532 + (Math.random() - 0.5) * 0.1,
        lng: -79.3832 + (Math.random() - 0.5) * 0.1
      } : null,
      status,
      videoId: null,
      incidentCount: 0,
      distractionCount: 0,
      drowsinessCount: 0,
      crashDetected: Math.random() < 0.1,
      createdAt: startTime.toISOString()
    });
    
    // Create incidents for completed trips
    if (status === 'completed') {
      const incidentTypes = ['distraction', 'drowsiness', 'speeding'];
      const numIncidents = Math.floor(Math.random() * 5);
      
      for (let j = 0; j < numIncidents; j++) {
        const type = incidentTypes[Math.floor(Math.random() * incidentTypes.length)];
        const incidentTime = new Date(startTime.getTime() + Math.random() * duration * 1000);
        
        let details = {};
        let severity = 'low';
        
        if (type === 'distraction') {
          details = {
            reason: faker.helpers.arrayElement(['phone', 'looking_away', 'eating']),
            duration: Math.random() * 6 + 2
          };
          severity = faker.helpers.arrayElement(['low', 'medium', 'high']);
          trip.distractionCount++;
        } else if (type === 'drowsiness') {
          details = {
            earValue: Math.random() * 0.1 + 0.15,
            duration: Math.random() * 12 + 3,
            eyesClosed: true
          };
          severity = faker.helpers.arrayElement(['medium', 'high', 'critical']);
          trip.drowsinessCount++;
        } else if (type === 'speeding') {
          const speedLimit = faker.helpers.arrayElement([50, 60, 80, 100]);
          const speed = speedLimit + Math.random() * 40 + 10;
          details = {
            speed,
            speedLimit,
            over: speed - speedLimit
          };
          severity = speed - speedLimit > 30 ? 'high' : 'medium';
        }
        
        create('incidents', {
          tripId: trip.id,
          userId: user.id,
          type,
          severity,
          timestamp: incidentTime.toISOString(),
          location: {
            lat: trip.startLocation.lat + (Math.random() - 0.5) * 0.01,
            lng: trip.startLocation.lng + (Math.random() - 0.5) * 0.01
          },
          speed: Math.random() * 60 + 40,
          details,
          videoTimestamp: Math.random() * duration,
          resolved: false
        });
        
        trip.incidentCount++;
      }
      
      // Update trip with incident counts
      update('trips', trip.id, {
        incidentCount: trip.incidentCount,
        distractionCount: trip.distractionCount,
        drowsinessCount: trip.drowsinessCount
      });
      
      // Create video for some trips
      if (Math.random() < 0.6) {
        const video = create('videos', {
          tripId: trip.id,
          userId: user.id,
          filename: `trip_${trip.id}_${Date.now()}.mp4`,
          size: Math.floor(Math.random() * 150000000) + 50000000,
          duration,
          format: 'MP4',
          resolution: '1920x1080',
          fps: 30,
          uploadedAt: endTime.toISOString(),
          url: `https://mock-s3.safedrive.ai/videos/${trip.id}.mp4`
        });
        
        update('trips', trip.id, { videoId: video.id });
      }
    }
  }
  
  console.log(`✅ Seeded ${db.users.size} users, ${db.trips.size} trips, ${db.incidents.size} incidents, ${db.videos.size} videos`);
}

/**
 * Reset database
 */

export async function resetData() {
  db.users.clear();
  db.trips.clear();
  db.incidents.clear();
  db.videos.clear();
  db.sessions.clear();
  
  await seedData();
}
