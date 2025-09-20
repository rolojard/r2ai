#!/usr/bin/env python3
"""
R2D2 Person Detection and Recognition System
Integrated system for real-time person detection, face recognition, and character identification
with 7-day memory management and Star Wars character recognition
"""

import cv2
import numpy as np
import torch
import json
import time
import logging
import threading
import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import queue
import face_recognition
import dlib
from ultralytics import YOLO
import asyncio
import websockets
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PersonDetection:
    """Person detection result"""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    class_name: str
    track_id: Optional[int] = None

@dataclass
class FaceDetection:
    """Face detection with quality assessment"""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    quality_score: float
    landmarks: Optional[np.ndarray] = None
    embedding: Optional[np.ndarray] = None
    embedding_hash: Optional[str] = None

@dataclass
class PersonIdentity:
    """Complete person identity with recognition status"""
    person_id: str
    identity_type: str  # 'new', 'temporary', 'persistent', 'star_wars_character'
    first_seen: datetime
    last_seen: datetime
    visit_count: int
    costume_type: Optional[str] = None
    character_name: Optional[str] = None
    familiarity_level: int = 1  # 1=stranger, 2=acquaintance, 3=friend, 4=close_friend, 5=best_friend
    interaction_history: List[Dict] = None
    preferred_responses: List[str] = None
    recognition_confidence: float = 0.0

    def __post_init__(self):
        if self.interaction_history is None:
            self.interaction_history = []
        if self.preferred_responses is None:
            self.preferred_responses = []

class R2D2PersonRecognitionSystem:
    """Integrated person detection and recognition system for R2D2"""

    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()

        # Initialize components
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.yolo_model = None
        self.face_detector = None
        self.running = False

        # Memory management
        self.temp_memory_days = 7
        self.db_path = "/home/rolo/r2ai/r2d2_person_memory.db"

        # Privacy and security
        self.privacy_salt = self._load_or_create_salt()

        # Processing queues
        self.detection_queue = queue.Queue(maxsize=10)
        self.recognition_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.Queue(maxsize=10)

        # Performance tracking
        self.performance_stats = {
            'fps': 0,
            'detections_per_sec': 0,
            'recognition_time': 0,
            'total_persons_detected': 0,
            'unique_faces_recognized': 0,
            'star_wars_characters_detected': 0
        }

        # Star Wars character database
        self.star_wars_characters = self._load_star_wars_characters()

        # Initialize system
        self._initialize_models()
        self._setup_database()

        logger.info("R2D2 Person Recognition System initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "person_detection": {
                "confidence_threshold": 0.7,
                "iou_threshold": 0.45,
                "max_detections": 10
            },
            "face_recognition": {
                "face_quality_threshold": 0.4,
                "similarity_threshold": 0.6,
                "min_face_size": 64
            },
            "memory_management": {
                "temp_retention_days": 7,
                "max_temp_identities": 1000,
                "cleanup_interval_hours": 6
            },
            "privacy": {
                "hash_embeddings": True,
                "auto_cleanup": True,
                "consent_required": False  # Convention setting
            },
            "performance": {
                "target_fps": 15,
                "detection_interval": 2,  # Process every Nth frame
                "max_concurrent_recognitions": 3
            }
        }

    def _load_or_create_salt(self) -> str:
        """Load or create privacy salt for embedding hashing"""
        salt_file = Path("/home/rolo/r2ai/.privacy_salt")

        if salt_file.exists():
            with open(salt_file, 'r') as f:
                return f.read().strip()
        else:
            salt = secrets.token_hex(32)
            salt_file.parent.mkdir(parents=True, exist_ok=True)
            with open(salt_file, 'w') as f:
                f.write(salt)
            return salt

    def _initialize_models(self):
        """Initialize YOLO and face recognition models"""
        try:
            # Load YOLO model for person detection
            logger.info("Loading YOLOv8 model for person detection...")
            self.yolo_model = YOLO('/home/rolo/r2ai/yolov8n.pt')

            if torch.cuda.is_available():
                self.yolo_model.to('cuda')
                logger.info("YOLO model loaded on GPU")
            else:
                logger.info("YOLO model loaded on CPU")

            # Configure YOLO for optimal performance
            self.yolo_model.overrides['verbose'] = False
            self.yolo_model.overrides['conf'] = self.config['person_detection']['confidence_threshold']
            self.yolo_model.overrides['iou'] = self.config['person_detection']['iou_threshold']

            # Initialize face detection
            logger.info("Initializing face detection models...")
            self.face_detector = dlib.get_frontal_face_detector()

            # Try to load shape predictor for landmarks
            predictor_path = "/home/rolo/r2ai/models/shape_predictor_68_face_landmarks.dat"
            self.landmark_predictor = None
            if Path(predictor_path).exists():
                self.landmark_predictor = dlib.shape_predictor(predictor_path)
                logger.info("Face landmark predictor loaded")

            logger.info("All models initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def _setup_database(self):
        """Setup SQLite database for person memory management"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                # Person identities table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS person_identities (
                        person_id TEXT PRIMARY KEY,
                        identity_type TEXT NOT NULL,
                        embedding_hash TEXT UNIQUE,
                        first_seen TIMESTAMP,
                        last_seen TIMESTAMP,
                        visit_count INTEGER DEFAULT 1,
                        costume_type TEXT,
                        character_name TEXT,
                        familiarity_level INTEGER DEFAULT 1,
                        interaction_data TEXT,
                        preferred_responses TEXT,
                        recognition_confidence REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Star Wars characters table (persistent)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS star_wars_characters (
                        character_id TEXT PRIMARY KEY,
                        character_name TEXT NOT NULL,
                        character_type TEXT,
                        costume_indicators TEXT,
                        recognition_features TEXT,
                        preferred_r2d2_responses TEXT,
                        canonical_info TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Interaction history table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS interaction_history (
                        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        person_id TEXT,
                        timestamp TIMESTAMP,
                        interaction_type TEXT,
                        r2d2_response TEXT,
                        effectiveness_score REAL,
                        costume_detected TEXT,
                        context_data TEXT,
                        FOREIGN KEY (person_id) REFERENCES person_identities (person_id)
                    )
                ''')

                # System performance tracking
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metric_type TEXT,
                        metric_value REAL,
                        context_data TEXT
                    )
                ''')

                conn.commit()
                logger.info("Database schema initialized")

        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise

    def _load_star_wars_characters(self) -> Dict:
        """Load Star Wars character recognition data"""
        return {
            "jedi": {
                "costume_indicators": ["lightsaber", "jedi_robe", "hood"],
                "recognition_features": ["brown_robe", "belt", "boots"],
                "responses": ["curious_beeps", "respectful_acknowledgment", "excited_whistles"],
                "familiarity_boost": 2
            },
            "sith": {
                "costume_indicators": ["red_lightsaber", "dark_robe", "hood"],
                "recognition_features": ["black_clothing", "cape", "mask"],
                "responses": ["cautious_warbles", "defensive_posture", "warning_beeps"],
                "familiarity_boost": 1
            },
            "stormtrooper": {
                "costume_indicators": ["white_armor", "helmet", "blaster"],
                "recognition_features": ["white_plastoid", "distinctive_helmet"],
                "responses": ["imperial_recognition", "neutral_beeps", "status_inquiry"],
                "familiarity_boost": 0
            },
            "rebel_pilot": {
                "costume_indicators": ["orange_suit", "helmet", "rebel_insignia"],
                "recognition_features": ["flight_suit", "helmet", "gloves"],
                "responses": ["excited_celebration", "alliance_solidarity", "mission_ready"],
                "familiarity_boost": 3
            },
            "princess_leia": {
                "costume_indicators": ["white_dress", "side_buns", "belt"],
                "recognition_features": ["iconic_hairstyle", "white_gown"],
                "responses": ["princess_respect", "mission_urgency", "protective_stance"],
                "familiarity_boost": 5
            }
        }

    def detect_persons(self, frame: np.ndarray) -> List[PersonDetection]:
        """Detect persons in frame using YOLO"""
        try:
            if self.yolo_model is None:
                return []

            # Run YOLO detection
            results = self.yolo_model(frame, verbose=False)
            detections = []

            if results and len(results) > 0:
                result = results[0]

                if result.boxes is not None:
                    boxes = result.boxes.cpu().numpy()

                    for box in boxes:
                        # Extract box information
                        x1, y1, x2, y2 = box.xyxy[0]
                        confidence = box.conf[0]
                        class_id = int(box.cls[0])
                        class_name = self.yolo_model.names[class_id]

                        # Only process person detections
                        if class_name == "person" and confidence >= self.config['person_detection']['confidence_threshold']:
                            detection = PersonDetection(
                                bbox=(int(x1), int(y1), int(x2-x1), int(y2-y1)),
                                confidence=float(confidence),
                                class_name=class_name
                            )
                            detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"Error in person detection: {e}")
            return []

    def detect_faces_in_person(self, frame: np.ndarray, person_bbox: Tuple[int, int, int, int]) -> List[FaceDetection]:
        """Detect faces within person bounding box"""
        try:
            if self.face_detector is None:
                return []

            x, y, w, h = person_bbox
            # Expand person bbox slightly for better face detection
            expand_ratio = 0.1
            x_expand = max(0, int(x - w * expand_ratio))
            y_expand = max(0, int(y - h * expand_ratio))
            w_expand = min(frame.shape[1] - x_expand, int(w * (1 + 2 * expand_ratio)))
            h_expand = min(frame.shape[0] - y_expand, int(h * (1 + 2 * expand_ratio)))

            # Extract person region
            person_region = frame[y_expand:y_expand+h_expand, x_expand:x_expand+w_expand]
            gray_region = cv2.cvtColor(person_region, cv2.COLOR_BGR2GRAY)

            # Detect faces in person region
            faces = self.face_detector(gray_region)
            detections = []

            for face in faces:
                # Convert to absolute coordinates
                face_x = x_expand + face.left()
                face_y = y_expand + face.top()
                face_w = face.width()
                face_h = face.height()

                # Quality assessment
                face_crop = frame[face_y:face_y+face_h, face_x:face_x+face_w]
                quality_score = self._assess_face_quality(face_crop)

                if quality_score >= self.config['face_recognition']['face_quality_threshold']:
                    # Generate face embedding
                    embedding = self._generate_face_embedding(face_crop)
                    embedding_hash = None

                    if embedding is not None:
                        embedding_hash = self._hash_embedding(embedding)

                    detection = FaceDetection(
                        bbox=(face_x, face_y, face_w, face_h),
                        confidence=1.0,  # dlib doesn't provide confidence
                        quality_score=quality_score,
                        embedding=embedding,
                        embedding_hash=embedding_hash
                    )
                    detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            return []

    def _assess_face_quality(self, face_crop: np.ndarray) -> float:
        """Assess face image quality for recognition reliability"""
        try:
            if face_crop.size == 0:
                return 0.0

            h, w = face_crop.shape[:2]

            # Size check
            if h < self.config['face_recognition']['min_face_size'] or w < self.config['face_recognition']['min_face_size']:
                return 0.1

            # Convert to grayscale for analysis
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

            # Blur assessment using Laplacian variance
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_quality = min(blur_score / 500.0, 1.0)

            # Brightness assessment
            brightness = np.mean(gray)
            brightness_quality = 1.0 - abs(brightness - 128) / 128.0

            # Contrast assessment
            contrast = gray.std()
            contrast_quality = min(contrast / 50.0, 1.0)

            # Combined quality score
            quality = (blur_quality * 0.4 + brightness_quality * 0.3 + contrast_quality * 0.3)
            return max(0.0, min(1.0, quality))

        except Exception as e:
            logger.error(f"Error assessing face quality: {e}")
            return 0.0

    def _generate_face_embedding(self, face_crop: np.ndarray) -> Optional[np.ndarray]:
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

    def _hash_embedding(self, embedding: np.ndarray) -> str:
        """Create privacy-preserving hash of face embedding"""
        try:
            # Convert embedding to bytes
            embedding_bytes = embedding.astype(np.float32).tobytes()

            # Create hash with salt
            hasher = hashlib.sha256()
            hasher.update(self.privacy_salt.encode())
            hasher.update(embedding_bytes)

            return hasher.hexdigest()

        except Exception as e:
            logger.error(f"Error hashing embedding: {e}")
            return ""

    def recognize_person(self, face_detection: FaceDetection) -> Optional[PersonIdentity]:
        """Recognize person from face detection"""
        try:
            if face_detection.embedding_hash is None:
                return None

            # Check for existing identity
            existing_identity = self._find_existing_identity(face_detection.embedding, face_detection.embedding_hash)

            if existing_identity:
                # Update existing identity
                return self._update_person_visit(existing_identity)
            else:
                # Create new temporary identity
                return self._create_new_identity(face_detection.embedding_hash)

        except Exception as e:
            logger.error(f"Error in person recognition: {e}")
            return None

    def _find_existing_identity(self, embedding: np.ndarray, embedding_hash: str) -> Optional[str]:
        """Find existing person identity by embedding similarity"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.temp_memory_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check for exact hash match first (most efficient)
                cursor.execute('''
                    SELECT person_id FROM person_identities
                    WHERE embedding_hash = ? AND last_seen > ?
                ''', (embedding_hash, cutoff_time))

                result = cursor.fetchone()
                if result:
                    return result[0]

                # If no exact match, check similarity with recent identities
                # This would require storing actual embeddings temporarily for comparison
                # For now, we'll rely on hash matching for privacy compliance

            return None

        except Exception as e:
            logger.error(f"Error finding existing identity: {e}")
            return None

    def _create_new_identity(self, embedding_hash: str) -> PersonIdentity:
        """Create new temporary person identity"""
        try:
            person_id = f"temp_{int(time.time())}_{np.random.randint(1000, 9999)}"
            current_time = datetime.now()

            identity = PersonIdentity(
                person_id=person_id,
                identity_type="temporary",
                first_seen=current_time,
                last_seen=current_time,
                visit_count=1,
                familiarity_level=1,  # Stranger
                recognition_confidence=0.8
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO person_identities (
                        person_id, identity_type, embedding_hash, first_seen, last_seen,
                        visit_count, familiarity_level, recognition_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    person_id, "temporary", embedding_hash, current_time, current_time,
                    1, 1, 0.8
                ))
                conn.commit()

            logger.info(f"Created new temporary identity: {person_id}")
            return identity

        except Exception as e:
            logger.error(f"Error creating new identity: {e}")
            return None

    def _update_person_visit(self, person_id: str) -> Optional[PersonIdentity]:
        """Update existing person identity with new visit"""
        try:
            current_time = datetime.now()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get current person data
                cursor.execute('''
                    SELECT visit_count, familiarity_level, first_seen, identity_type,
                           costume_type, character_name
                    FROM person_identities WHERE person_id = ?
                ''', (person_id,))

                result = cursor.fetchone()
                if not result:
                    return None

                visit_count, familiarity_level, first_seen, identity_type, costume_type, character_name = result

                # Update visit count and familiarity
                new_visit_count = visit_count + 1
                new_familiarity_level = self._calculate_familiarity_level(new_visit_count)

                # Update database
                conn.execute('''
                    UPDATE person_identities SET
                        last_seen = ?,
                        visit_count = ?,
                        familiarity_level = ?
                    WHERE person_id = ?
                ''', (current_time, new_visit_count, new_familiarity_level, person_id))

                conn.commit()

                # Create updated identity
                identity = PersonIdentity(
                    person_id=person_id,
                    identity_type=identity_type,
                    first_seen=datetime.fromisoformat(first_seen) if isinstance(first_seen, str) else first_seen,
                    last_seen=current_time,
                    visit_count=new_visit_count,
                    costume_type=costume_type,
                    character_name=character_name,
                    familiarity_level=new_familiarity_level,
                    recognition_confidence=0.9
                )

                logger.info(f"Updated person {person_id}, visit count: {new_visit_count}, familiarity: {new_familiarity_level}")
                return identity

        except Exception as e:
            logger.error(f"Error updating person visit: {e}")
            return None

    def _calculate_familiarity_level(self, visit_count: int) -> int:
        """Calculate familiarity level based on visit count"""
        if visit_count == 1:
            return 1  # Stranger
        elif visit_count <= 3:
            return 2  # Acquaintance
        elif visit_count <= 7:
            return 3  # Friend
        elif visit_count <= 15:
            return 4  # Close friend
        else:
            return 5  # Best friend

    def detect_star_wars_character(self, frame: np.ndarray, person_bbox: Tuple[int, int, int, int]) -> Optional[str]:
        """Detect Star Wars character based on costume analysis"""
        try:
            # This is a simplified implementation
            # In a full system, this would use specialized costume detection models

            x, y, w, h = person_bbox
            person_region = frame[y:y+h, x:x+w]

            # Analyze colors and shapes for character detection
            # This is a placeholder - would need trained models for accurate detection

            # Basic color analysis
            hsv = cv2.cvtColor(person_region, cv2.COLOR_BGR2HSV)

            # Simple heuristics (would be replaced with proper ML models)
            white_mask = cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))
            white_ratio = np.sum(white_mask) / (w * h * 255)

            brown_mask = cv2.inRange(hsv, (10, 50, 20), (20, 255, 200))
            brown_ratio = np.sum(brown_mask) / (w * h * 255)

            black_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 50))
            black_ratio = np.sum(black_mask) / (w * h * 255)

            # Basic character detection heuristics
            if white_ratio > 0.4:
                return "stormtrooper"
            elif brown_ratio > 0.3:
                return "jedi"
            elif black_ratio > 0.5:
                return "sith"

            return None

        except Exception as e:
            logger.error(f"Error in character detection: {e}")
            return None

    def generate_r2d2_response(self, person_identity: PersonIdentity) -> Dict[str, Any]:
        """Generate appropriate R2D2 response based on person identity"""
        try:
            familiarity = person_identity.familiarity_level
            character = person_identity.character_name

            # Base response on familiarity level
            if familiarity == 1:  # Stranger
                response_type = "curious_cautious"
                excitement_level = "low"
            elif familiarity == 2:  # Acquaintance
                response_type = "friendly_recognition"
                excitement_level = "medium"
            elif familiarity == 3:  # Friend
                response_type = "warm_greeting"
                excitement_level = "medium_high"
            elif familiarity >= 4:  # Close friend or best friend
                response_type = "enthusiastic_welcome"
                excitement_level = "high"

            # Modify based on Star Wars character
            if character:
                character_data = self.star_wars_characters.get(character, {})
                character_responses = character_data.get("responses", [])
                if character_responses:
                    response_type = np.random.choice(character_responses)

                # Apply familiarity boost for Star Wars characters
                familiarity_boost = character_data.get("familiarity_boost", 0)
                if familiarity_boost > 0:
                    excitement_level = "very_high"

            response = {
                "response_type": response_type,
                "excitement_level": excitement_level,
                "familiarity_context": {
                    "level": familiarity,
                    "visit_count": person_identity.visit_count,
                    "is_returning": person_identity.visit_count > 1
                },
                "character_context": {
                    "detected_character": character,
                    "is_star_wars": character is not None
                },
                "recommended_actions": {
                    "audio": response_type,
                    "movement": self._get_movement_for_response(response_type),
                    "lights": self._get_lights_for_response(response_type, excitement_level)
                }
            }

            return response

        except Exception as e:
            logger.error(f"Error generating R2D2 response: {e}")
            return {"response_type": "default_friendly", "excitement_level": "medium"}

    def _get_movement_for_response(self, response_type: str) -> str:
        """Get appropriate movement for response type"""
        movement_map = {
            "curious_cautious": "head_tilt_slow",
            "friendly_recognition": "dome_turn_acknowledge",
            "warm_greeting": "happy_wiggle",
            "enthusiastic_welcome": "excited_dance",
            "respectful_acknowledgment": "formal_bow",
            "cautious_warbles": "defensive_posture",
            "excited_celebration": "victory_spin"
        }
        return movement_map.get(response_type, "gentle_movement")

    def _get_lights_for_response(self, response_type: str, excitement_level: str) -> str:
        """Get appropriate light pattern for response"""
        if excitement_level == "very_high":
            return "rainbow_celebration"
        elif excitement_level == "high":
            return "bright_pulse"
        elif excitement_level == "medium_high":
            return "warm_glow"
        elif excitement_level == "medium":
            return "gentle_blue"
        else:
            return "subtle_indicators"

    def cleanup_old_identities(self):
        """Clean up old temporary identities for privacy compliance"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.temp_memory_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete old temporary identities
                cursor.execute('''
                    DELETE FROM person_identities
                    WHERE identity_type = 'temporary' AND last_seen < ?
                ''', (cutoff_time,))
                deleted_count = cursor.rowcount

                # Delete orphaned interactions
                cursor.execute('''
                    DELETE FROM interaction_history
                    WHERE person_id NOT IN (SELECT person_id FROM person_identities)
                ''')

                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Privacy cleanup: removed {deleted_count} old temporary identities")

        except Exception as e:
            logger.error(f"Error in privacy cleanup: {e}")

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process a single frame for person detection and recognition"""
        try:
            start_time = time.time()

            # Step 1: Detect persons
            person_detections = self.detect_persons(frame)

            # Step 2: Process each detected person
            recognition_results = []

            for person_detection in person_detections:
                # Detect faces in person
                face_detections = self.detect_faces_in_person(frame, person_detection.bbox)

                # Detect Star Wars character (if applicable)
                character = self.detect_star_wars_character(frame, person_detection.bbox)

                # Process each face
                for face_detection in face_detections:
                    # Recognize person
                    person_identity = self.recognize_person(face_detection)

                    if person_identity:
                        # Update character info if detected
                        if character:
                            person_identity.character_name = character

                        # Generate R2D2 response
                        r2d2_response = self.generate_r2d2_response(person_identity)

                        recognition_result = {
                            "person_detection": asdict(person_detection),
                            "face_detection": {
                                "bbox": face_detection.bbox,
                                "confidence": face_detection.confidence,
                                "quality_score": face_detection.quality_score
                            },
                            "person_identity": asdict(person_identity),
                            "r2d2_response": r2d2_response,
                            "character_detected": character
                        }

                        recognition_results.append(recognition_result)

            # Update performance stats
            processing_time = time.time() - start_time
            self.performance_stats['recognition_time'] = processing_time
            self.performance_stats['total_persons_detected'] += len(person_detections)

            result = {
                "timestamp": datetime.now().isoformat(),
                "frame_shape": frame.shape,
                "processing_time": processing_time,
                "person_count": len(person_detections),
                "recognition_count": len(recognition_results),
                "results": recognition_results,
                "performance_stats": self.performance_stats.copy()
            }

            return result

        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count identities by type
                cursor.execute('SELECT identity_type, COUNT(*) FROM person_identities GROUP BY identity_type')
                identity_counts = dict(cursor.fetchall())

                # Count recent interactions
                recent_time = datetime.now() - timedelta(hours=24)
                cursor.execute('SELECT COUNT(*) FROM interaction_history WHERE timestamp > ?', (recent_time,))
                recent_interactions = cursor.fetchone()[0]

                # Get system uptime (simplified)
                uptime_hours = (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds() / 3600

            status = {
                "system_status": "active" if self.running else "inactive",
                "models_loaded": {
                    "yolo": self.yolo_model is not None,
                    "face_detector": self.face_detector is not None
                },
                "memory_stats": {
                    "identity_counts": identity_counts,
                    "temp_retention_days": self.temp_memory_days,
                    "recent_interactions_24h": recent_interactions
                },
                "performance_stats": self.performance_stats.copy(),
                "config": self.config,
                "uptime_hours": uptime_hours,
                "device": str(self.device)
            }

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}

def main():
    """Main function for testing the person recognition system"""
    print("R2D2 Person Recognition System")
    print("=" * 50)

    # Initialize system
    recognition_system = R2D2PersonRecognitionSystem()

    # Test with webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    print("Starting person recognition test...")
    print("Press 'q' to quit, 's' for system status")

    try:
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error reading frame")
                break

            # Process every 3rd frame for performance
            frame_count += 1
            if frame_count % 3 == 0:
                result = recognition_system.process_frame(frame)

                # Draw results on frame
                if "results" in result:
                    for recognition in result["results"]:
                        person_bbox = recognition["person_detection"]["bbox"]
                        face_bbox = recognition["face_detection"]["bbox"]
                        identity = recognition["person_identity"]

                        # Draw person bounding box
                        x, y, w, h = person_bbox
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                        # Draw face bounding box
                        fx, fy, fw, fh = face_bbox
                        cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (255, 0, 0), 2)

                        # Add labels
                        label = f"Visits: {identity['visit_count']}, Level: {identity['familiarity_level']}"
                        if identity['character_name']:
                            label += f", Char: {identity['character_name']}"

                        cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Display frame
            cv2.imshow('R2D2 Person Recognition', frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                status = recognition_system.get_system_status()
                print(f"\nSystem Status: {json.dumps(status, indent=2, default=str)}\n")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        recognition_system.cleanup_old_identities()
        print("Person recognition system stopped")

if __name__ == "__main__":
    main()