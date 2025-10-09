-- ================================================================
-- DATABASE BLUEPRINT FOR VEHICLE DETECTION & POLLUTION MONITORING SYSTEM
-- ================================================================
-- Created: October 5, 2025
-- Purpose: REFERENCE ONLY - Database table definitions for future reference
-- 
-- ⚠️  IMPORTANT: This file is for REFERENCE PURPOSES ONLY
-- ⚠️  DO NOT execute this file directly
-- ⚠️  Use this as documentation to understand table structures
-- 
-- Contains table definitions for:
-- - Vehicle detection and speed monitoring
-- - User management and authentication  
-- - Pollution tracking by location and date
-- - Blacklist management
-- - System settings
-- ================================================================

-- Database creation (if needed)
-- CREATE DATABASE IF NOT EXISTS numberplates_speed;
-- USE numberplates_speed;

-- ================================================================
-- CORE TABLES
-- ================================================================

-- Blacklisted vehicles table
CREATE TABLE blacklisted_vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numberplate VARCHAR(255) NOT NULL,
    reason TEXT
);

-- Vehicle detection and speed monitoring data
CREATE TABLE my_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date VARCHAR(255),
    time VARCHAR(255),
    track_id INT,
    class_name VARCHAR(255),
    speed FLOAT,
    numberplate VARCHAR(255),
    status VARCHAR(255)
);

-- System settings for speed thresholds
CREATE TABLE settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    threshold_speed FLOAT NOT NULL
);

-- Users table for authentication and user management
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Vehicle pollution data based on fuel type and emission rates
CREATE TABLE vehicle_pollution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numberplate VARCHAR(255) NOT NULL UNIQUE,
    fuel_type ENUM('petrol', 'diesel', 'electric', 'CNG', 'hybrid') NOT NULL,
    emission_rate FLOAT NOT NULL                     -- grams of CO₂ per km
);

-- Location-based emission tracking and analytics
CREATE TABLE location_emission (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_pollution FLOAT DEFAULT 0,       -- total g/km emitted by all vehicles at this location for that date
    vehicles_passed INT DEFAULT 0,         -- number of vehicles recorded at this location for that date
    avg_speed FLOAT DEFAULT 0,             -- average speed of vehicles at that location for that date
    UNIQUE KEY (location, date)            -- ensures one record per location per date
);

-- Temporary vehicle tracking for video processing sessions
CREATE TABLE temp_vehicle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numberplate VARCHAR(255) NOT NULL UNIQUE,
    video_filename VARCHAR(255),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INITIAL DATA INSERTION
-- ================================================================

-- Insert default speed threshold
INSERT INTO settings (threshold_speed) VALUES (50); -- Default threshold speed

-- ================================================================
-- END OF DATABASE BLUEPRINT
-- ================================================================