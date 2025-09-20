# R2D2 Guest Recognition System with Short-Term Memory

## System Overview
The guest recognition system enables R2D2 to identify and remember convention attendees for several days, creating personalized interactions that enhance the immersive experience.

## Technical Architecture

### Hardware Requirements
- **Camera**: Logitech C920e (1080p) for face detection
- **Processing**: Nvidia Orin Nano with CUDA acceleration
- **Storage**: Local SSD for face embeddings and interaction history
- **Memory**: 4GB allocated for real-time processing

### Software Stack
- **Face Detection**: OpenCV DNN or MediaPipe Face Detection
- **Face Recognition**: FaceNet or ArcFace for embedding generation
- **Database**: SQLite for lightweight local storage
- **Framework**: Python with PyTorch/TensorRT optimization

## Core Components

### 1. Face Detection Pipeline
```python
class FaceDetector:
    """Real-time face detection optimized for Orin Nano"""

    def __init__(self):
        self.detector = cv2.dnn.readNetFromTensorflow(
            'opencv_face_detector_uint8.pb',
            'opencv_face_detector.pbtxt'
        )
        self.confidence_threshold = 0.7

    def detect_faces(self, frame):
        """Detect faces in video frame"""
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123])
        self.detector.setInput(blob)
        detections = self.detector.forward()

        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence_threshold:
                # Extract bounding box coordinates
                h, w = frame.shape[:2]
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                faces.append(box.astype("int"))

        return faces
```

### 2. Face Recognition Engine
```python
class FaceRecognizer:
    """Face embedding generation and matching"""

    def __init__(self):
        # Load pre-trained FaceNet model optimized for TensorRT
        self.model = torch.jit.load('facenet_tensorrt.pt')
        self.embedding_dim = 512
        self.similarity_threshold = 0.6

    def generate_embedding(self, face_image):
        """Generate 512-dimensional face embedding"""
        # Preprocess face image
        face_tensor = self.preprocess_face(face_image)

        with torch.no_grad():
            embedding = self.model(face_tensor)

        return embedding.cpu().numpy().flatten()

    def calculate_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between embeddings"""
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return similarity
```

### 3. Guest Memory Database
```sql
-- SQLite schema for guest recognition
CREATE TABLE guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    face_embedding BLOB,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_count INTEGER DEFAULT 1,
    costume_tags TEXT,  -- JSON array of detected costumes
    personality_notes TEXT,  -- R2D2's observations
    preferred_responses TEXT  -- JSON array of effective interactions
);

CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_type TEXT,  -- greeting, excitement, curiosity, etc.
    costume_detected TEXT,  -- jedi, sith, rebel, etc.
    r2d2_response TEXT,  -- audio/movement sequence used
    effectiveness_score REAL,  -- crowd reaction analysis
    FOREIGN KEY (guest_id) REFERENCES guests (id)
);
```

### 4. Memory Management System
```python
class GuestMemoryManager:
    """Manages short-term guest memory and interactions"""

    def __init__(self, db_path="r2d2_memory.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.setup_database()
        self.memory_retention_days = 7  # Convention plus buffer

    def register_guest(self, face_embedding, costume_tags=None):
        """Register new guest or update existing"""
        # Check if guest already exists
        existing_guest = self.find_matching_guest(face_embedding)

        if existing_guest:
            # Update existing guest
            self.update_guest_visit(existing_guest['id'], costume_tags)
            return existing_guest['id']
        else:
            # Create new guest entry
            return self.create_new_guest(face_embedding, costume_tags)

    def find_matching_guest(self, face_embedding):
        """Find matching guest using embedding similarity"""
        cursor = self.db.cursor()
        cursor.execute("SELECT id, face_embedding FROM guests WHERE last_seen > datetime('now', '-7 days')")

        for guest_id, stored_embedding_blob in cursor.fetchall():
            stored_embedding = np.frombuffer(stored_embedding_blob, dtype=np.float32)
            similarity = self.calculate_similarity(face_embedding, stored_embedding)

            if similarity > 0.6:  # Similarity threshold
                return {
                    'id': guest_id,
                    'similarity': similarity,
                    'embedding': stored_embedding
                }

        return None
```

## R2D2 Personality Integration

### Interaction Patterns Based on Guest History

#### First-Time Visitor
```python
def handle_new_guest(guest_id, costume_type):
    """R2D2's response to new guests"""
    responses = {
        'jedi': {
            'audio': 'curious_beeps_sequence',
            'movement': 'head_tilt_inspection',
            'lights': 'blue_pulse_pattern'
        },
        'sith': {
            'audio': 'cautious_warble_sequence',
            'movement': 'defensive_posture',
            'lights': 'red_warning_pattern'
        },
        'rebel': {
            'audio': 'excited_whistles',
            'movement': 'enthusiastic_dome_spin',
            'lights': 'orange_celebration'
        }
    }

    return responses.get(costume_type, responses['default'])
```

#### Returning Visitor
```python
def handle_returning_guest(guest_id, visit_count, costume_type):
    """R2D2's personalized response to returning guests"""
    if visit_count == 2:
        # "Oh, it's you again!" - recognition response
        return {
            'audio': 'recognition_happy_beeps',
            'movement': 'excited_panel_flutter',
            'lights': 'rainbow_acknowledgment'
        }
    elif visit_count > 2:
        # "My old friend!" - familiar response
        return {
            'audio': 'familiar_friend_sounds',
            'movement': 'warm_greeting_sequence',
            'lights': 'gentle_pulse_welcome'
        }
```

### Behavioral Learning System
```python
class R2D2BehaviorLearning:
    """Learn effective responses based on crowd reactions"""

    def analyze_interaction_effectiveness(self, interaction_id):
        """Analyze crowd reaction using audio analysis"""
        # Measure crowd noise level, laughter, cheering
        # Use microphone input to gauge response
        effectiveness_score = self.measure_crowd_response()

        # Update database with effectiveness rating
        self.update_interaction_score(interaction_id, effectiveness_score)

    def recommend_response(self, guest_profile, context):
        """Suggest R2D2 response based on learned patterns"""
        # Query historical interactions for similar contexts
        similar_interactions = self.find_similar_interactions(guest_profile, context)

        # Weight responses by effectiveness scores
        best_response = self.select_optimal_response(similar_interactions)

        return best_response
```

## Privacy and Ethics

### Data Protection
- **Local Storage Only**: No cloud uploads or external data sharing
- **Automatic Purging**: 7-day retention policy with automatic deletion
- **Anonymized Data**: No personal information stored, only face embeddings
- **Opt-Out Capability**: Clear signage and opt-out mechanism

### Consent Management
```python
class ConsentManager:
    """Handle guest consent for recognition system"""

    def __init__(self):
        self.opt_out_faces = set()  # Track users who opted out

    def check_consent(self, face_embedding):
        """Check if guest has opted out of recognition"""
        # Quick similarity check against opt-out database
        for opt_out_embedding in self.opt_out_faces:
            if self.calculate_similarity(face_embedding, opt_out_embedding) > 0.8:
                return False
        return True

    def register_opt_out(self, face_embedding):
        """Register guest opt-out request"""
        self.opt_out_faces.add(face_embedding)
        # Also remove from main guest database
        self.remove_guest_data(face_embedding)
```

## Performance Optimization

### Real-Time Processing Pipeline
1. **Frame Capture**: 30 FPS from C920e camera
2. **Face Detection**: Process every 3rd frame (10 FPS detection)
3. **Recognition**: Process detected faces in parallel threads
4. **Memory Lookup**: Optimized embedding similarity search
5. **Response Generation**: Immediate R2D2 behavior trigger

### CUDA Acceleration
- **TensorRT**: Optimized face recognition model
- **GPU Memory**: Efficient batch processing
- **Parallel Processing**: Multiple face processing streams

## Integration with R2D2 Systems

### Behavior Coordination
```python
class GuestInteractionCoordinator:
    """Coordinate guest recognition with R2D2 behaviors"""

    def process_guest_interaction(self, detected_faces, costume_context):
        """Main interaction processing loop"""
        for face in detected_faces:
            # Generate face embedding
            embedding = self.face_recognizer.generate_embedding(face)

            # Check guest memory
            guest_info = self.memory_manager.register_guest(embedding, costume_context)

            # Generate appropriate R2D2 response
            response = self.behavior_engine.generate_response(guest_info, costume_context)

            # Execute coordinated R2D2 behavior
            self.execute_r2d2_response(response)

            # Log interaction for learning
            self.log_interaction(guest_info, response)
```

This guest recognition system enables R2D2 to create meaningful, personalized interactions while respecting privacy and maintaining authentic droid personality characteristics.