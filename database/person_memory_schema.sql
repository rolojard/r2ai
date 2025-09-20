-- R2D2 Person Recognition Memory Database Schema
-- SQLite database for privacy-compliant person recognition and memory management
-- File: /home/rolo/r2ai/r2d2_person_memory.db

-- =====================================================
-- CORE PERSON IDENTITY MANAGEMENT
-- =====================================================

-- Primary table for person identities with privacy-preserving design
CREATE TABLE IF NOT EXISTS person_identities (
    person_id TEXT PRIMARY KEY,                    -- Unique identifier (temp_timestamp_random or persistent_id)
    identity_type TEXT NOT NULL CHECK (identity_type IN ('temporary', 'persistent', 'star_wars_character')),
    embedding_hash TEXT UNIQUE,                    -- SHA256 hash of face embedding (privacy-preserving)
    first_seen TIMESTAMP NOT NULL,                 -- First detection timestamp
    last_seen TIMESTAMP NOT NULL,                  -- Most recent detection timestamp
    visit_count INTEGER DEFAULT 1,                 -- Number of separate visits/interactions
    costume_type TEXT,                             -- Detected costume category
    character_name TEXT,                           -- Star Wars character name (if detected)
    familiarity_level INTEGER DEFAULT 1 CHECK (familiarity_level BETWEEN 1 AND 5),  -- 1=stranger, 5=best_friend
    interaction_data TEXT,                         -- JSON blob of interaction metadata
    preferred_responses TEXT,                      -- JSON array of preferred R2D2 response types
    recognition_confidence REAL DEFAULT 0.0 CHECK (recognition_confidence BETWEEN 0.0 AND 1.0),
    is_convention_staff BOOLEAN DEFAULT FALSE,     -- Special flag for convention staff
    notes TEXT,                                    -- Optional notes (convention context)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookups by embedding hash (primary recognition query)
CREATE INDEX IF NOT EXISTS idx_person_embedding_hash ON person_identities(embedding_hash);

-- Index for memory cleanup operations (temporal queries)
CREATE INDEX IF NOT EXISTS idx_person_last_seen ON person_identities(last_seen);

-- Index for familiarity level queries
CREATE INDEX IF NOT EXISTS idx_person_familiarity ON person_identities(familiarity_level);

-- Index for character detection queries
CREATE INDEX IF NOT EXISTS idx_person_character ON person_identities(character_name) WHERE character_name IS NOT NULL;

-- =====================================================
-- STAR WARS CHARACTER DEFINITIONS
-- =====================================================

-- Master table for Star Wars character recognition patterns
CREATE TABLE IF NOT EXISTS star_wars_characters (
    character_id TEXT PRIMARY KEY,                 -- Unique character identifier
    character_name TEXT NOT NULL,                  -- Display name (e.g., "Jedi Knight", "Stormtrooper")
    character_type TEXT NOT NULL,                  -- Category (jedi, sith, rebel, imperial, etc.)
    costume_indicators TEXT NOT NULL,              -- JSON array of visual detection criteria
    recognition_features TEXT NOT NULL,            -- JSON object with detection parameters
    preferred_r2d2_responses TEXT NOT NULL,        -- JSON array of appropriate response types
    canonical_info TEXT,                          -- Character background and context
    detection_confidence_threshold REAL DEFAULT 0.7,  -- Minimum confidence for character detection
    familiarity_boost INTEGER DEFAULT 0,          -- Automatic familiarity level boost
    is_active BOOLEAN DEFAULT TRUE,               -- Enable/disable character detection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate default Star Wars characters
INSERT OR REPLACE INTO star_wars_characters VALUES
('jedi', 'Jedi Knight', 'jedi',
 '["lightsaber", "jedi_robe", "hood", "belt", "boots"]',
 '{"color_ranges": {"brown": [10, 50, 20, 20, 255, 200], "beige": [15, 30, 50, 25, 255, 255]}, "shape_features": ["flowing_robe", "belt"], "confidence_multiplier": 1.2}',
 '["curious_beeps", "respectful_acknowledgment", "excited_whistles", "force_recognition"]',
 'Jedi are peacekeepers of the galaxy, wielding lightsabers and the Force.',
 0.7, 2, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('sith', 'Sith Lord', 'sith',
 '["red_lightsaber", "dark_robe", "hood", "cape", "mask"]',
 '{"color_ranges": {"black": [0, 0, 0, 180, 255, 50], "red": [0, 50, 50, 10, 255, 255]}, "shape_features": ["cape", "hood"], "confidence_multiplier": 1.1}',
 '["cautious_warbles", "defensive_posture", "warning_beeps", "imperial_recognition"]',
 'Sith are dark side Force users, enemies of the Jedi Order.',
 0.75, 1, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('stormtrooper', 'Imperial Stormtrooper', 'imperial',
 '["white_armor", "helmet", "blaster", "utility_belt"]',
 '{"color_ranges": {"white": [0, 0, 200, 180, 30, 255]}, "shape_features": ["distinctive_helmet", "armor_segments"], "confidence_multiplier": 1.3}',
 '["imperial_recognition", "neutral_beeps", "status_inquiry", "protocol_acknowledgment"]',
 'Elite soldiers of the Galactic Empire, known for their white armor.',
 0.8, 0, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('rebel_pilot', 'Rebel Alliance Pilot', 'rebel',
 '["orange_suit", "helmet", "rebel_insignia", "life_support"]',
 '{"color_ranges": {"orange": [5, 100, 100, 25, 255, 255]}, "shape_features": ["flight_helmet", "suit_panels"], "confidence_multiplier": 1.2}',
 '["excited_celebration", "alliance_solidarity", "mission_ready", "victory_beeps"]',
 'Brave pilots of the Rebel Alliance fighting against the Empire.',
 0.75, 3, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('princess_leia', 'Princess Leia', 'rebel',
 '["white_dress", "side_buns", "belt", "royal_bearing"]',
 '{"color_ranges": {"white": [0, 0, 200, 180, 30, 255]}, "shape_features": ["iconic_hairstyle", "flowing_gown"], "confidence_multiplier": 1.4}',
 '["princess_respect", "mission_urgency", "protective_stance", "royal_acknowledgment"]',
 'Princess of Alderaan and key leader of the Rebel Alliance.',
 0.8, 5, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- =====================================================
-- INTERACTION HISTORY TRACKING
-- =====================================================

-- Detailed log of all R2D2 interactions with recognized persons
CREATE TABLE IF NOT EXISTS interaction_history (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,                       -- Reference to person_identities
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_type TEXT NOT NULL,                -- Type of interaction (greeting, character_response, etc.)
    r2d2_response TEXT NOT NULL,                   -- Specific response type executed
    response_duration REAL,                       -- Duration of response sequence (seconds)
    effectiveness_score REAL CHECK (effectiveness_score BETWEEN 0.0 AND 1.0),  -- Response effectiveness (if measurable)
    costume_detected TEXT,                         -- Character costume detected during interaction
    context_data TEXT,                            -- JSON blob with interaction context
    environmental_factors TEXT,                   -- JSON blob (lighting, crowd, noise level)
    recognition_confidence REAL,                  -- Confidence level of person recognition
    character_confidence REAL,                    -- Confidence level of character detection
    audience_size INTEGER DEFAULT 1,              -- Number of people in vicinity
    venue_location TEXT,                          -- Convention hall, booth area, etc.
    FOREIGN KEY (person_id) REFERENCES person_identities (person_id) ON DELETE CASCADE
);

-- Index for person-specific interaction history
CREATE INDEX IF NOT EXISTS idx_interaction_person ON interaction_history(person_id);

-- Index for temporal interaction analysis
CREATE INDEX IF NOT EXISTS idx_interaction_timestamp ON interaction_history(timestamp);

-- Index for response effectiveness analysis
CREATE INDEX IF NOT EXISTS idx_interaction_effectiveness ON interaction_history(effectiveness_score) WHERE effectiveness_score IS NOT NULL;

-- =====================================================
-- PERFORMANCE MONITORING
-- =====================================================

-- System performance metrics and monitoring data
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_type TEXT NOT NULL,                     -- Type of metric (fps, latency, accuracy, etc.)
    metric_value REAL NOT NULL,                    -- Numeric value of the metric
    metric_unit TEXT,                             -- Unit of measurement (ms, fps, percentage)
    context_data TEXT,                            -- JSON blob with additional context
    system_load REAL,                            -- Overall system load at time of measurement
    memory_usage_mb REAL,                        -- Memory usage in megabytes
    gpu_utilization REAL,                        -- GPU utilization percentage
    queue_depths TEXT,                           -- JSON object with queue depth information
    error_count INTEGER DEFAULT 0,               -- Number of errors in measurement period
    component TEXT                               -- System component (detection, recognition, database)
);

-- Index for performance trend analysis
CREATE INDEX IF NOT EXISTS idx_performance_type_time ON performance_metrics(metric_type, timestamp);

-- Index for system health monitoring
CREATE INDEX IF NOT EXISTS idx_performance_errors ON performance_metrics(error_count) WHERE error_count > 0;

-- =====================================================
-- SYSTEM CONFIGURATION
-- =====================================================

-- Configuration parameters for the recognition system
CREATE TABLE IF NOT EXISTS system_configuration (
    config_id TEXT PRIMARY KEY,                   -- Configuration parameter name
    config_value TEXT NOT NULL,                   -- Parameter value (JSON for complex values)
    config_type TEXT NOT NULL CHECK (config_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,                             -- Human-readable description
    is_runtime_modifiable BOOLEAN DEFAULT TRUE,   -- Can be changed without restart
    validation_rules TEXT,                       -- JSON object with validation criteria
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by TEXT DEFAULT 'system'
);

-- Insert default configuration
INSERT OR REPLACE INTO system_configuration VALUES
('person_detection.confidence_threshold', '0.7', 'number', 'YOLO person detection confidence threshold', TRUE, '{"min": 0.1, "max": 0.95}', CURRENT_TIMESTAMP, 'system'),
('face_recognition.similarity_threshold', '0.6', 'number', 'Face recognition similarity threshold', TRUE, '{"min": 0.3, "max": 0.9}', CURRENT_TIMESTAMP, 'system'),
('face_recognition.quality_threshold', '0.4', 'number', 'Minimum face quality for processing', TRUE, '{"min": 0.1, "max": 0.8}', CURRENT_TIMESTAMP, 'system'),
('memory.temp_retention_days', '7', 'number', 'Days to retain temporary identities', TRUE, '{"min": 1, "max": 30}', CURRENT_TIMESTAMP, 'system'),
('memory.max_temp_identities', '1000', 'number', 'Maximum temporary identities to store', TRUE, '{"min": 100, "max": 10000}', CURRENT_TIMESTAMP, 'system'),
('performance.target_fps', '15', 'number', 'Target frames per second for recognition', TRUE, '{"min": 5, "max": 30}', CURRENT_TIMESTAMP, 'system'),
('privacy.auto_cleanup_enabled', 'true', 'boolean', 'Enable automatic privacy cleanup', TRUE, '{}', CURRENT_TIMESTAMP, 'system'),
('character_detection.enabled', 'true', 'boolean', 'Enable Star Wars character detection', TRUE, '{}', CURRENT_TIMESTAMP, 'system');

-- =====================================================
-- PRIVACY AND COMPLIANCE
-- =====================================================

-- Privacy compliance tracking and audit log
CREATE TABLE IF NOT EXISTS privacy_audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation_type TEXT NOT NULL,                  -- 'create', 'access', 'update', 'delete', 'cleanup'
    affected_records INTEGER DEFAULT 1,           -- Number of records affected
    data_type TEXT NOT NULL,                      -- 'identity', 'interaction', 'embedding_hash'
    retention_policy_applied TEXT,               -- Which retention policy was applied
    compliance_framework TEXT,                   -- GDPR, CCPA, etc.
    user_consent_status TEXT,                    -- 'given', 'withdrawn', 'not_required'
    anonymization_method TEXT,                   -- Method used for data anonymization
    audit_details TEXT                          -- JSON blob with detailed audit information
);

-- Index for compliance reporting
CREATE INDEX IF NOT EXISTS idx_privacy_audit_timestamp ON privacy_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_privacy_audit_operation ON privacy_audit_log(operation_type);

-- =====================================================
-- DATA MAINTENANCE VIEWS
-- =====================================================

-- View for identities requiring cleanup (privacy compliance)
CREATE VIEW IF NOT EXISTS identities_for_cleanup AS
SELECT
    person_id,
    identity_type,
    last_seen,
    JULIANDAY('now') - JULIANDAY(last_seen) as days_since_seen,
    visit_count,
    familiarity_level
FROM person_identities
WHERE identity_type = 'temporary'
AND JULIANDAY('now') - JULIANDAY(last_seen) > 7;

-- View for system performance summary
CREATE VIEW IF NOT EXISTS performance_summary AS
SELECT
    metric_type,
    COUNT(*) as measurement_count,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    MAX(timestamp) as last_measured
FROM performance_metrics
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY metric_type;

-- View for interaction effectiveness analysis
CREATE VIEW IF NOT EXISTS interaction_effectiveness AS
SELECT
    p.character_name,
    p.familiarity_level,
    COUNT(i.interaction_id) as interaction_count,
    AVG(i.effectiveness_score) as avg_effectiveness,
    i.r2d2_response,
    COUNT(DISTINCT i.person_id) as unique_persons
FROM interaction_history i
JOIN person_identities p ON i.person_id = p.person_id
WHERE i.effectiveness_score IS NOT NULL
GROUP BY p.character_name, p.familiarity_level, i.r2d2_response;

-- =====================================================
-- TRIGGERS FOR DATA INTEGRITY
-- =====================================================

-- Automatically update the updated_at timestamp for person_identities
CREATE TRIGGER IF NOT EXISTS update_person_timestamp
AFTER UPDATE ON person_identities
BEGIN
    UPDATE person_identities SET updated_at = CURRENT_TIMESTAMP WHERE person_id = NEW.person_id;
END;

-- Log privacy-relevant operations
CREATE TRIGGER IF NOT EXISTS log_identity_creation
AFTER INSERT ON person_identities
BEGIN
    INSERT INTO privacy_audit_log (operation_type, data_type, affected_records, audit_details)
    VALUES ('create', 'identity', 1, json_object('person_id', NEW.person_id, 'identity_type', NEW.identity_type));
END;

CREATE TRIGGER IF NOT EXISTS log_identity_deletion
AFTER DELETE ON person_identities
BEGIN
    INSERT INTO privacy_audit_log (operation_type, data_type, affected_records, audit_details)
    VALUES ('delete', 'identity', 1, json_object('person_id', OLD.person_id, 'identity_type', OLD.identity_type, 'reason', 'cleanup'));
END;

-- =====================================================
-- STORED PROCEDURES (SQLITE COMPATIBLE)
-- =====================================================

-- Note: SQLite doesn't support stored procedures, but we can create
-- prepared statements for common operations. These would be implemented
-- in the Python application layer.

-- Common queries that should be prepared:
-- 1. find_person_by_hash(embedding_hash)
-- 2. update_person_visit(person_id)
-- 3. cleanup_old_identities(days_threshold)
-- 4. get_interaction_history(person_id, limit)
-- 5. log_performance_metric(type, value, context)

-- =====================================================
-- DATABASE OPTIMIZATION
-- =====================================================

-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode = WAL;

-- Optimize for performance
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
PRAGMA temp_store = MEMORY;

-- Analyze tables for query optimization
ANALYZE;

-- =====================================================
-- INITIAL DATA VALIDATION
-- =====================================================

-- Verify character data integrity
SELECT 'Character validation:' as check_type,
       COUNT(*) as character_count,
       COUNT(DISTINCT character_type) as unique_types
FROM star_wars_characters;

-- Verify configuration completeness
SELECT 'Configuration validation:' as check_type,
       COUNT(*) as config_count,
       COUNT(CASE WHEN config_value IS NULL THEN 1 END) as null_values
FROM system_configuration;

-- Database schema version for migration tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR REPLACE INTO schema_version VALUES
('1.0.0', CURRENT_TIMESTAMP, 'Initial person recognition schema');

-- End of schema definition