# SafeDrive AI - Database Schema Design

## Overview
This document defines the database schema for SafeDrive AI backend.

---

## Tables

### 1. users
Stores user account information.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique user ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| full_name | VARCHAR(255) | NOT NULL | User's full name |
| phone_number | VARCHAR(20) | NULL | User's phone number |
| created_at | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

---

### 2. trips
Stores driving trip information.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique trip ID |
| user_id | INTEGER | FOREIGN KEY (users.id) | User who took the trip |
| start_time | TIMESTAMP | NOT NULL | Trip start time |
| end_time | TIMESTAMP | NULL | Trip end time |
| distance_km | DECIMAL(10,2) | NULL | Distance traveled in km |
| start_location | VARCHAR(255) | NULL | Starting address |
| end_location | VARCHAR(255) | NULL | Ending address |
| safety_score | INTEGER | NULL | Safety score (0-100) |
| status | VARCHAR(50) | DEFAULT 'active' | Trip status (active, completed) |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

---

### 3. incidents
Stores distraction and crash events during trips.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique incident ID |
| trip_id | INTEGER | FOREIGN KEY (trips.id) | Related trip |
| incident_type | VARCHAR(50) | NOT NULL | Type: distraction, crash, drowsiness |
| severity | VARCHAR(20) | NOT NULL | Severity: low, medium, high |
| timestamp | TIMESTAMP | NOT NULL | When incident occurred |
| latitude | DECIMAL(10,8) | NULL | GPS latitude |
| longitude | DECIMAL(11,8) | NULL | GPS longitude |
| description | TEXT | NULL | Additional details |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

---

### 4. videos
Stores video file metadata and S3 references.

| Column Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique video ID |
| incident_id | INTEGER | FOREIGN KEY (incidents.id) | Related incident |
| s3_bucket | VARCHAR(255) | NOT NULL | S3 bucket name |
| s3_key | VARCHAR(500) | NOT NULL | S3 object key (path) |
| file_size_mb | DECIMAL(10,2) | NULL | File size in MB |
| duration_seconds | INTEGER | NULL | Video duration |
| resolution | VARCHAR(20) | NULL | Video resolution (e.g., 1080p) |
| uploaded_at | TIMESTAMP | DEFAULT NOW() | Upload timestamp |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |

---

## Relationships

- **users → trips**: One user can have many trips (1:N)
- **trips → incidents**: One trip can have many incidents (1:N)
- **incidents → videos**: One incident can have one video (1:1)

---

## Indexes (for performance)

- `users.email` - Fast user lookup by email
- `trips.user_id` - Fast trip queries by user
- `incidents.trip_id` - Fast incident queries by trip
- `videos.incident_id` - Fast video lookup by incident

---

## Notes

- All timestamps are stored in UTC
- Password is hashed using bcrypt before storage
- Videos are stored in AWS S3, only metadata in database
- Safety scores calculated based on incident count and severity
