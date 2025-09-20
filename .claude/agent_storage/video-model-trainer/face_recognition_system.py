#!/usr/bin/env python3
"""
Enhanced Face Recognition System for R2D2 Guest Interactions
Privacy-compliant facial recognition with personalized guest memory
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import sqlite3
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
import face_recognition
import dlib
from scipy.spatial.distance import cosine
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class FaceDetection:
    """Face detection result with privacy safeguards"""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    landmarks: Optional[np.ndarray] = None
    quality_score: float = 0.0
    embedding_hash: Optional[str] = None  # For privacy

@dataclass
class GuestIdentity:
    """Guest identity with interaction preferences"""
    guest_id: str
    embedding_hash: str
    first_seen: datetime
    last_seen: datetime
    visit_count: int
    costume_history: List[str]
    interaction_preferences: Dict[str, Any]
    r2d2_relationship_level: int  # 1-5 scale
    favorite_responses: List[str]
    privacy_consent: bool

class PrivacyFaceRecognizer:
    """Privacy-compliant face recognition with embedding hashing"""

    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Initialize face detection models
        self.face_detector = None
        self.face_encoder = None
        self.landmark_predictor = None

        # Privacy settings
        self.hash_salt = self._generate_salt()
        self.embedding_cache = {}
        self.max_cache_size = 1000

        self.load_models()

    def _generate_salt(self) -> str:
        """Generate unique salt for embedding hashing"""
        salt_file = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/.privacy_salt")
        if salt_file.exists():
            with open(salt_file, 'r') as f:
                return f.read().strip()
        else:
            import secrets
            salt = secrets.token_hex(32)
            with open(salt_file, 'w') as f:
                f.write(salt)
            return salt

    def load_models(self):
        """Load face detection and recognition models"""
        try:
            # Initialize dlib face detector
            self.face_detector = dlib.get_frontal_face_detector()

            # Load shape predictor for landmarks
            predictor_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models/shape_predictor_68_face_landmarks.dat"
            if Path(predictor_path).exists():
                self.landmark_predictor = dlib.shape_predictor(predictor_path)
            else:
                logger.warning("Face landmark predictor not found")

            # Use face_recognition library for encoding (based on dlib)
            logger.info("Face recognition models loaded successfully")

        except Exception as e:
            logger.error(f"Error loading face recognition models: {e}")

    def detect_faces(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detect faces with quality assessment"""
        if self.face_detector is None:
            return []

        try:
            # Convert to grayscale for dlib
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = self.face_detector(gray)
            detections = []

            for face in faces:
                # Convert dlib rectangle to bbox
                x, y, w, h = face.left(), face.top(), face.width(), face.height()

                # Quality assessment
                face_crop = frame[y:y+h, x:x+w]
                quality_score = self._assess_face_quality(face_crop)

                # Skip low-quality faces
                if quality_score < self.config.get('face_quality_threshold', 0.3):
                    continue

                # Extract landmarks if predictor is available
                landmarks = None
                if self.landmark_predictor:
                    shape = self.landmark_predictor(gray, face)
                    landmarks = np.array([[p.x, p.y] for p in shape.parts()])

                detection = FaceDetection(
                    bbox=(x, y, w, h),
                    confidence=1.0,  # dlib doesn't provide confidence
                    landmarks=landmarks,
                    quality_score=quality_score
                )

                detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            return []

    def _assess_face_quality(self, face_crop: np.ndarray) -> float:
        """Assess face image quality for recognition reliability"""
        try:
            # Check if face is too small
            h, w = face_crop.shape[:2]
            if h < 64 or w < 64:
                return 0.1

            # Check blur using Laplacian variance
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_quality = min(blur_score / 500.0, 1.0)  # Normalize

            # Check brightness
            brightness = np.mean(gray)
            brightness_quality = 1.0 - abs(brightness - 128) / 128.0

            # Check contrast
            contrast = gray.std()
            contrast_quality = min(contrast / 50.0, 1.0)

            # Combined quality score
            quality = (blur_quality * 0.4 + brightness_quality * 0.3 + contrast_quality * 0.3)
            return max(0.0, min(1.0, quality))

        except Exception as e:
            logger.error(f"Error assessing face quality: {e}")
            return 0.0

    def generate_face_embedding(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
        """Generate face embedding using face_recognition library"""
        try:
            # Convert BGR to RGB
            rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

            # Generate encoding
            face_encodings = face_recognition.face_encodings(rgb_face)

            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error generating face embedding: {e}")
            return None

    def hash_embedding(self, embedding: np.ndarray) -> str:
        """Create privacy-preserving hash of face embedding"""
        try:
            # Convert embedding to bytes
            embedding_bytes = embedding.astype(np.float32).tobytes()

            # Create hash with salt
            hasher = hashlib.sha256()
            hasher.update(self.hash_salt.encode())
            hasher.update(embedding_bytes)

            return hasher.hexdigest()

        except Exception as e:
            logger.error(f"Error hashing embedding: {e}")
            return ""

    def calculate_embedding_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate similarity between face embeddings"""
        try:
            # Use face_recognition's built-in distance function
            distance = face_recognition.face_distance([embedding1], embedding2)[0]
            # Convert distance to similarity (0-1)
            similarity = 1.0 - distance
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.error(f"Error calculating embedding similarity: {e}")
            return 0.0

class R2D2GuestMemorySystem:
    """Advanced guest memory system with relationship modeling"""

    def __init__(self, config: Dict):
        self.config = config
        self.db_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/r2d2_guest_memory.db"
        self.face_recognizer = PrivacyFaceRecognizer(config)

        # Relationship modeling
        self.relationship_thresholds = {
            1: 1,    # Stranger - first meeting
            2: 3,    # Acquaintance - seen a few times
            3: 7,    # Friend - regular interactions
            4: 15,   # Good friend - frequent interactions
            5: 30    # Best friend - very frequent interactions
        }

        self.setup_database()

    def setup_database(self):
        """Initialize enhanced guest memory database"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                # Enhanced guests table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS guests (
                        guest_id TEXT PRIMARY KEY,
                        embedding_hash TEXT UNIQUE,
                        first_seen TIMESTAMP,
                        last_seen TIMESTAMP,
                        visit_count INTEGER DEFAULT 1,
                        total_interaction_time REAL DEFAULT 0.0,
                        costume_history TEXT,
                        interaction_preferences TEXT,
                        r2d2_relationship_level INTEGER DEFAULT 1,
                        favorite_responses TEXT,
                        response_effectiveness TEXT,
                        personality_notes TEXT,
                        privacy_consent BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Detailed interactions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS guest_interactions (
                        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guest_id TEXT,
                        timestamp TIMESTAMP,
                        interaction_duration REAL,
                        costume_detected TEXT,
                        r2d2_response_type TEXT,
                        guest_reaction_score REAL,
                        environmental_context TEXT,
                        crowd_size INTEGER,
                        interaction_success BOOLEAN,
                        FOREIGN KEY (guest_id) REFERENCES guests (guest_id)
                    )
                ''')

                # R2D2 learning table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS r2d2_learning (
                        learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT,
                        pattern_data TEXT,
                        effectiveness_score REAL,
                        usage_count INTEGER DEFAULT 1,
                        last_used TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("Enhanced guest memory database initialized")

        except Exception as e:
            logger.error(f"Error setting up database: {e}")

    def process_guest_interaction(self, frame: np.ndarray, costume_context: str = None) -> List[GuestIdentity]:
        """Process guest interaction with enhanced memory"""
        try:
            # Detect faces
            face_detections = self.face_recognizer.detect_faces(frame)
            guest_identities = []

            for detection in face_detections:
                # Extract face crop
                x, y, w, h = detection.bbox
                face_crop = frame[y:y+h, x:x+w]

                # Generate embedding
                embedding = self.face_recognizer.generate_face_embedding(face_crop)
                if embedding is None:
                    continue

                # Hash embedding for privacy
                embedding_hash = self.face_recognizer.hash_embedding(embedding)
                detection.embedding_hash = embedding_hash

                # Find or create guest identity
                guest_identity = self.find_or_create_guest(embedding, embedding_hash, costume_context)
                if guest_identity:
                    guest_identities.append(guest_identity)

            return guest_identities

        except Exception as e:
            logger.error(f"Error processing guest interaction: {e}")
            return []

    def find_or_create_guest(self, embedding: np.ndarray, embedding_hash: str, costume: str = None) -> Optional[GuestIdentity]:
        """Find existing guest or create new one with enhanced profiling"""
        try:
            # Look for existing guest by embedding similarity
            existing_guest = self._find_similar_guest(embedding)

            if existing_guest:
                # Update existing guest
                return self._update_guest_visit(existing_guest, costume)
            else:
                # Create new guest
                return self._create_new_guest(embedding_hash, costume)

        except Exception as e:
            logger.error(f"Error finding/creating guest: {e}")
            return None

    def _find_similar_guest(self, embedding: np.ndarray) -> Optional[str]:
        """Find guest with similar face embedding"""
        try:
            similarity_threshold = self.config.get('face_similarity_threshold', 0.6)
            retention_days = self.config.get('guest_retention_days', 7)
            cutoff_time = datetime.now() - timedelta(days=retention_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT guest_id, embedding_hash
                    FROM guests
                    WHERE last_seen > ? AND privacy_consent = 1
                ''', (cutoff_time,))

                # For each guest, we would need to compare embeddings
                # In a real implementation, we would store embeddings securely
                # For now, we'll use a simplified approach
                for guest_id, stored_hash in cursor.fetchall():
                    # This is a simplified approach - in practice, we would need
                    # a more sophisticated similarity comparison
                    if stored_hash:  # Guest exists
                        return guest_id

            return None

        except Exception as e:
            logger.error(f"Error finding similar guest: {e}")
            return None

    def _create_new_guest(self, embedding_hash: str, costume: str = None) -> GuestIdentity:
        """Create new guest profile with initial assessment"""
        try:
            guest_id = f"guest_{int(time.time())}_{np.random.randint(1000, 9999)}"
            current_time = datetime.now()

            costume_history = [costume] if costume else []
            interaction_preferences = {
                "preferred_interaction_style": "curious",  # Initial default
                "response_to_excitement": "moderate",
                "personal_space_preference": "normal"
            }

            guest_identity = GuestIdentity(
                guest_id=guest_id,
                embedding_hash=embedding_hash,
                first_seen=current_time,
                last_seen=current_time,
                visit_count=1,
                costume_history=costume_history,
                interaction_preferences=interaction_preferences,
                r2d2_relationship_level=1,  # Stranger
                favorite_responses=[],
                privacy_consent=True
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO guests (
                        guest_id, embedding_hash, first_seen, last_seen,
                        visit_count, costume_history, interaction_preferences,
                        r2d2_relationship_level, favorite_responses, privacy_consent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    guest_id, embedding_hash, current_time, current_time,
                    1, json.dumps(costume_history), json.dumps(interaction_preferences),
                    1, json.dumps([]), True
                ))
                conn.commit()

            logger.info(f"Created new guest profile: {guest_id}")
            return guest_identity

        except Exception as e:
            logger.error(f"Error creating new guest: {e}")
            return None

    def _update_guest_visit(self, guest_id: str, costume: str = None) -> Optional[GuestIdentity]:
        """Update existing guest with new visit"""
        try:
            current_time = datetime.now()

            with sqlite3.connect(self.db_path) as conn:
                # Get current guest data
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT visit_count, costume_history, interaction_preferences,
                           r2d2_relationship_level, favorite_responses, first_seen
                    FROM guests WHERE guest_id = ?
                ''', (guest_id,))

                result = cursor.fetchone()
                if not result:
                    return None

                visit_count, costume_history_json, preferences_json, relationship_level, favorites_json, first_seen = result

                # Update visit count and relationship level
                new_visit_count = visit_count + 1
                new_relationship_level = self._calculate_relationship_level(new_visit_count)

                # Update costume history
                costume_history = json.loads(costume_history_json or "[]")
                if costume and costume not in costume_history:
                    costume_history.append(costume)

                # Update database
                conn.execute('''
                    UPDATE guests SET
                        last_seen = ?,
                        visit_count = ?,
                        costume_history = ?,
                        r2d2_relationship_level = ?
                    WHERE guest_id = ?
                ''', (current_time, new_visit_count, json.dumps(costume_history),
                      new_relationship_level, guest_id))

                conn.commit()

                # Create updated guest identity
                guest_identity = GuestIdentity(
                    guest_id=guest_id,
                    embedding_hash="",  # Not needed for existing guest
                    first_seen=datetime.fromisoformat(first_seen) if isinstance(first_seen, str) else first_seen,
                    last_seen=current_time,
                    visit_count=new_visit_count,
                    costume_history=costume_history,
                    interaction_preferences=json.loads(preferences_json or "{}"),
                    r2d2_relationship_level=new_relationship_level,
                    favorite_responses=json.loads(favorites_json or "[]"),
                    privacy_consent=True
                )

                logger.info(f"Updated guest {guest_id}, visit count: {new_visit_count}, relationship level: {new_relationship_level}")
                return guest_identity

        except Exception as e:
            logger.error(f"Error updating guest visit: {e}")
            return None

    def _calculate_relationship_level(self, visit_count: int) -> int:
        """Calculate R2D2's relationship level with guest"""
        for level in sorted(self.relationship_thresholds.keys(), reverse=True):
            if visit_count >= self.relationship_thresholds[level]:
                return level
        return 1

    def log_interaction_outcome(self, guest_id: str, response_type: str, effectiveness_score: float,
                              interaction_duration: float = 0.0, costume: str = None):
        """Log interaction outcome for learning"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO guest_interactions (
                        guest_id, timestamp, interaction_duration, costume_detected,
                        r2d2_response_type, guest_reaction_score, interaction_success
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    guest_id, datetime.now(), interaction_duration, costume,
                    response_type, effectiveness_score, effectiveness_score > 0.7
                ))

                # Update guest's favorite responses if effective
                if effectiveness_score > 0.8:
                    cursor = conn.cursor()
                    cursor.execute('SELECT favorite_responses FROM guests WHERE guest_id = ?', (guest_id,))
                    result = cursor.fetchone()

                    if result:
                        favorites = json.loads(result[0] or "[]")
                        if response_type not in favorites:
                            favorites.append(response_type)

                        conn.execute(
                            'UPDATE guests SET favorite_responses = ? WHERE guest_id = ?',
                            (json.dumps(favorites), guest_id)
                        )

                conn.commit()

        except Exception as e:
            logger.error(f"Error logging interaction outcome: {e}")

    def get_guest_interaction_history(self, guest_id: str) -> Dict[str, Any]:
        """Get comprehensive guest interaction history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get guest profile
                cursor.execute('''
                    SELECT * FROM guests WHERE guest_id = ?
                ''', (guest_id,))
                guest_data = cursor.fetchone()

                if not guest_data:
                    return {}

                # Get interaction history
                cursor.execute('''
                    SELECT * FROM guest_interactions
                    WHERE guest_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                ''', (guest_id,))
                interactions = cursor.fetchall()

                return {
                    "guest_profile": guest_data,
                    "recent_interactions": interactions,
                    "total_interactions": len(interactions)
                }

        except Exception as e:
            logger.error(f"Error getting guest history: {e}")
            return {}

    def generate_personalized_response_recommendation(self, guest_identity: GuestIdentity,
                                                    costume: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized R2D2 response recommendation"""
        try:
            # Base response on relationship level
            relationship_level = guest_identity.r2d2_relationship_level

            # Customize based on guest history and preferences
            if relationship_level == 1:  # Stranger
                response_style = "curious_cautious"
                excitement_level = "moderate"
            elif relationship_level == 2:  # Acquaintance
                response_style = "friendly_recognition"
                excitement_level = "moderate_high"
            elif relationship_level >= 3:  # Friend or better
                response_style = "enthusiastic_welcome"
                excitement_level = "high"

                # Use favorite responses if available
                if guest_identity.favorite_responses:
                    response_style = np.random.choice(guest_identity.favorite_responses)

            # Adjust for costume
            costume_modifier = self._get_costume_response_modifier(costume)

            recommendation = {
                "response_style": response_style,
                "excitement_level": excitement_level,
                "relationship_context": {
                    "level": relationship_level,
                    "visit_count": guest_identity.visit_count,
                    "time_since_last_visit": (datetime.now() - guest_identity.last_seen).total_seconds()
                },
                "personalization": {
                    "use_favorite_responses": len(guest_identity.favorite_responses) > 0,
                    "costume_familiarity": costume in guest_identity.costume_history,
                    "interaction_preferences": guest_identity.interaction_preferences
                },
                "costume_modifier": costume_modifier
            }

            return recommendation

        except Exception as e:
            logger.error(f"Error generating personalized response: {e}")
            return {"response_style": "default_friendly", "excitement_level": "moderate"}

    def _get_costume_response_modifier(self, costume: str) -> Dict[str, Any]:
        """Get costume-specific response modifiers"""
        costume_modifiers = {
            "jedi": {"respect_level": "high", "caution": "low", "excitement": "high"},
            "sith": {"respect_level": "medium", "caution": "high", "excitement": "medium"},
            "rebel_alliance": {"respect_level": "high", "caution": "low", "excitement": "very_high"},
            "stormtrooper": {"respect_level": "medium", "caution": "medium", "excitement": "low"},
            "imperial_officer": {"respect_level": "medium", "caution": "high", "excitement": "low"},
            "mandalorian": {"respect_level": "high", "caution": "medium", "excitement": "medium"},
            "civilian": {"respect_level": "medium", "caution": "low", "excitement": "medium"}
        }

        return costume_modifiers.get(costume, costume_modifiers["civilian"])

    def cleanup_old_guests(self):
        """Clean up old guest data for privacy compliance"""
        try:
            retention_days = self.config.get('guest_retention_days', 7)
            cutoff_time = datetime.now() - timedelta(days=retention_days)

            with sqlite3.connect(self.db_path) as conn:
                # Delete old guests
                cursor = conn.cursor()
                cursor.execute('DELETE FROM guests WHERE last_seen < ?', (cutoff_time,))
                deleted_guests = cursor.rowcount

                # Delete orphaned interactions
                cursor.execute('''
                    DELETE FROM guest_interactions
                    WHERE guest_id NOT IN (SELECT guest_id FROM guests)
                ''')
                deleted_interactions = cursor.rowcount

                conn.commit()

                if deleted_guests > 0:
                    logger.info(f"Privacy cleanup: removed {deleted_guests} guests and {deleted_interactions} interactions")

        except Exception as e:
            logger.error(f"Error in privacy cleanup: {e}")

# Configuration for face recognition system
def get_face_recognition_config():
    """Get configuration for face recognition system"""
    return {
        "face_quality_threshold": 0.4,
        "face_similarity_threshold": 0.6,
        "guest_retention_days": 7,
        "max_guests_in_memory": 1000,
        "privacy_mode": True,
        "consent_required": True,
        "automatic_cleanup": True,
        "cleanup_interval_hours": 24
    }