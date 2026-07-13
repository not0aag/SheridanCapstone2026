-- SafeDrive AI - Database Table Creation Script
-- Run this script to create all database tables

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS distraction_alerts CASCADE;
DROP TABLE IF EXISTS emergency_contacts CASCADE;
DROP TABLE IF EXISTS videos CASCADE;
DROP TABLE IF EXISTS incidents CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create trips table
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    distance_km DECIMAL(10,2),
    start_location VARCHAR(255),
    end_location VARCHAR(255),
    safety_score INTEGER CHECK (safety_score >= 0 AND safety_score <= 100),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create incidents table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    incident_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    timestamp TIMESTAMP NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- Create videos table
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    file_size_mb DECIMAL(10,2),
    duration_seconds INTEGER,
    resolution VARCHAR(20),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
);

-- Create emergency_contacts table
CREATE TABLE emergency_contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    relationship VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create distraction_alerts table
CREATE TABLE distraction_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    trip_id INTEGER,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    contacts_notified INTEGER NOT NULL DEFAULT 0,
    sent_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE SET NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_trips_start_time ON trips(start_time);
CREATE INDEX idx_incidents_trip_id ON incidents(trip_id);
CREATE INDEX idx_incidents_timestamp ON incidents(timestamp);
CREATE INDEX idx_videos_incident_id ON videos(incident_id);
CREATE INDEX idx_emergency_contacts_user_id ON emergency_contacts(user_id);
CREATE INDEX idx_distraction_alerts_user_id ON distraction_alerts(user_id);
CREATE INDEX idx_distraction_alerts_sent_at ON distraction_alerts(sent_at);

-- Display success message
SELECT 'Database tables created successfully!' AS status;
