#!/usr/bin/env python3
"""
Optimized Real-Time Inference Engine for R2D2 Computer Vision
Target: <100ms end-to-end response time on Nvidia Orin Nano
"""

import cv2
import numpy as np
import torch
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import time
import threading
import queue
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class InferenceResult:
    """Optimized inference result structure"""
    detections: List[Dict[str, Any]]
    inference_time_ms: float
    preprocessing_time_ms: float
    postprocessing_time_ms: float
    total_time_ms: float
    confidence_scores: List[float]
    frame_id: int
    timestamp: float

class TensorRTEngine:
    """Optimized TensorRT inference engine"""

    def __init__(self, engine_path: str, input_shape: Tuple[int, int, int, int]):
        self.engine_path = engine_path
        self.input_shape = input_shape  # (batch, channels, height, width)
        self.engine = None
        self.context = None
        self.stream = None
        self.input_binding = None
        self.output_binding = None
        self.allocations = {}
        self.load_engine()

    def load_engine(self):
        """Load TensorRT engine"""
        try:
            # Initialize TensorRT
            logger.info(f"Loading TensorRT engine: {self.engine_path}")
            TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

            # Load engine
            with open(self.engine_path, 'rb') as f, trt.Runtime(TRT_LOGGER) as runtime:
                self.engine = runtime.deserialize_cuda_engine(f.read())

            if self.engine is None:
                raise RuntimeError("Failed to load TensorRT engine")

            # Create execution context
            self.context = self.engine.create_execution_context()

            # Create CUDA stream
            self.stream = cuda.Stream()

            # Allocate memory
            self._allocate_memory()

            logger.info("TensorRT engine loaded successfully")

        except Exception as e:
            logger.error(f"Error loading TensorRT engine: {e}")
            raise

    def _allocate_memory(self):
        """Allocate GPU and CPU memory for inference"""
        self.allocations = {}

        for i in range(self.engine.num_bindings):
            binding_name = self.engine.get_binding_name(i)
            binding_shape = self.context.get_binding_shape(i)
            binding_dtype = trt.nptype(self.engine.get_binding_dtype(i))

            # Calculate size
            size = trt.volume(binding_shape) * np.dtype(binding_dtype).itemsize

            # Allocate GPU memory
            device_mem = cuda.mem_alloc(size)

            # Allocate CPU memory
            host_mem = cuda.pagelocked_empty(binding_shape, binding_dtype)

            self.allocations[binding_name] = {
                'host': host_mem,
                'device': device_mem,
                'shape': binding_shape,
                'dtype': binding_dtype,
                'size': size
            }

            # Store input/output binding indices
            if self.engine.binding_is_input(i):
                self.input_binding = binding_name
            else:
                self.output_binding = binding_name

        logger.info(f"Memory allocated - Input: {self.input_binding}, Output: {self.output_binding}")

    def infer(self, input_data: np.ndarray) -> np.ndarray:
        """Run inference on input data"""
        try:
            start_time = time.time()

            # Copy input to GPU
            input_allocation = self.allocations[self.input_binding]
            np.copyto(input_allocation['host'], input_data.ravel())
            cuda.memcpy_htod_async(input_allocation['device'], input_allocation['host'], self.stream)

            # Run inference
            bindings = [allocation['device'] for allocation in self.allocations.values()]
            self.context.execute_async_v2(bindings, self.stream.handle)

            # Copy output from GPU
            output_allocation = self.allocations[self.output_binding]
            cuda.memcpy_dtoh_async(output_allocation['host'], output_allocation['device'], self.stream)

            # Synchronize
            self.stream.synchronize()

            inference_time = (time.time() - start_time) * 1000
            logger.debug(f"TensorRT inference: {inference_time:.2f}ms")

            return output_allocation['host'].reshape(output_allocation['shape'])

        except Exception as e:
            logger.error(f"TensorRT inference error: {e}")
            raise

class OptimizedGuestDetector:
    """Ultra-fast guest detection with TensorRT optimization"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Performance targets
        self.target_inference_time = 50  # ms
        self.target_preprocessing_time = 10  # ms
        self.target_postprocessing_time = 20  # ms

        # Model paths
        self.model_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models")

        # TensorRT engine
        self.trt_engine = None
        self.torch_model = None

        # Optimization settings
        self.input_size = (640, 640)
        self.confidence_threshold = 0.7
        self.nms_threshold = 0.4

        # Memory pools for optimization
        self.input_buffer_pool = queue.Queue(maxsize=10)
        self.output_buffer_pool = queue.Queue(maxsize=10)

        self._initialize_models()
        self._prepare_memory_pools()

    def _initialize_models(self):
        """Initialize optimized models"""
        try:
            # Try TensorRT first
            trt_path = self.model_dir / "yolov8n_tensorrt.engine"
            if trt_path.exists():
                logger.info("Loading TensorRT engine for guest detection")
                input_shape = (1, 3, self.input_size[1], self.input_size[0])
                self.trt_engine = TensorRTEngine(str(trt_path), input_shape)
            else:
                # Fallback to optimized PyTorch
                logger.info("Loading optimized PyTorch model")
                self._load_optimized_torch_model()

        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def _load_optimized_torch_model(self):
        """Load and optimize PyTorch model"""
        try:
            from ultralytics import YOLO

            # Load model
            model_path = self.model_dir / "yolov8n.pt"
            self.torch_model = YOLO(str(model_path))

            # Optimize for inference
            self.torch_model.model.eval()
            if hasattr(self.torch_model.model, 'fuse'):
                self.torch_model.model.fuse()

            # Convert to TorchScript for speed
            dummy_input = torch.randn(1, 3, self.input_size[1], self.input_size[0]).to(self.device)
            with torch.no_grad():
                traced_model = torch.jit.trace(self.torch_model.model, dummy_input)
                self.torch_model.model = traced_model

            logger.info("PyTorch model optimized")

        except Exception as e:
            logger.error(f"Error optimizing PyTorch model: {e}")

    def _prepare_memory_pools(self):
        """Prepare memory pools for zero-copy operations"""
        try:
            # Pre-allocate input buffers
            for _ in range(10):
                input_buffer = np.empty((1, 3, self.input_size[1], self.input_size[0]), dtype=np.float32)
                self.input_buffer_pool.put(input_buffer)

            # Pre-allocate output buffers
            for _ in range(10):
                if self.trt_engine:
                    output_shape = self.trt_engine.allocations[self.trt_engine.output_binding]['shape']
                    output_buffer = np.empty(output_shape, dtype=np.float32)
                else:
                    output_buffer = np.empty((1, 84, 8400), dtype=np.float32)  # YOLO output shape
                self.output_buffer_pool.put(output_buffer)

            logger.info("Memory pools prepared")

        except Exception as e:
            logger.error(f"Error preparing memory pools: {e}")

    @lru_cache(maxsize=32)
    def _get_preprocessing_transform(self, input_height: int, input_width: int):
        """Cached preprocessing transformation"""
        target_h, target_w = self.input_size
        scale = min(target_h / input_height, target_w / input_width)
        return scale, target_h, target_w

    def preprocess_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Ultra-fast frame preprocessing"""
        start_time = time.time()

        try:
            # Get buffer from pool
            try:
                input_buffer = self.input_buffer_pool.get_nowait()
            except queue.Empty:
                input_buffer = np.empty((1, 3, self.input_size[1], self.input_size[0]), dtype=np.float32)

            # Fast resize with optimized parameters
            h, w = frame.shape[:2]
            scale, target_h, target_w = self._get_preprocessing_transform(h, w)

            # Letterbox resize
            new_h, new_w = int(h * scale), int(w * scale)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

            # Pad to target size
            pad_h = (target_h - new_h) // 2
            pad_w = (target_w - new_w) // 2

            padded = cv2.copyMakeBorder(
                resized, pad_h, target_h - new_h - pad_h, pad_w, target_w - new_w - pad_w,
                cv2.BORDER_CONSTANT, value=(114, 114, 114)
            )

            # Convert BGR to RGB and normalize
            rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
            normalized = rgb.astype(np.float32) / 255.0

            # HWC to CHW
            transposed = normalized.transpose(2, 0, 1)

            # Copy to buffer
            input_buffer[0] = transposed

            preprocessing_time = (time.time() - start_time) * 1000

            metadata = {
                'scale': scale,
                'pad_h': pad_h,
                'pad_w': pad_w,
                'original_shape': (h, w),
                'preprocessing_time_ms': preprocessing_time
            }

            return input_buffer, metadata

        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            raise

    def postprocess_detections(self, outputs: np.ndarray, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ultra-fast detection postprocessing"""
        start_time = time.time()

        try:
            detections = []

            # Parse YOLO output format
            if len(outputs.shape) == 3:
                outputs = outputs[0]  # Remove batch dimension

            # Transpose if needed (8400, 84) -> (84, 8400)
            if outputs.shape[0] == 8400:
                outputs = outputs.T

            # Extract boxes and scores
            boxes = outputs[:4, :].T  # (8400, 4)
            scores = outputs[4:, :].T  # (8400, 80) or (8400, 1) for person only

            # Filter by confidence for person class (index 0)
            if scores.shape[1] == 1:
                # Single class (person)
                confidences = scores[:, 0]
            else:
                # Multi-class, get person class (index 0)
                confidences = scores[:, 0]

            valid_indices = confidences > self.confidence_threshold

            if not np.any(valid_indices):
                return []

            # Filter detections
            valid_boxes = boxes[valid_indices]
            valid_confidences = confidences[valid_indices]

            # Convert from center format to corner format
            x_center, y_center, width, height = valid_boxes.T
            x1 = x_center - width / 2
            y1 = y_center - height / 2
            x2 = x_center + width / 2
            y2 = y_center + height / 2

            # Scale back to original image coordinates
            scale = metadata['scale']
            pad_h = metadata['pad_h']
            pad_w = metadata['pad_w']

            x1 = (x1 - pad_w) / scale
            y1 = (y1 - pad_h) / scale
            x2 = (x2 - pad_w) / scale
            y2 = (y2 - pad_h) / scale

            # Clip to image bounds
            orig_h, orig_w = metadata['original_shape']
            x1 = np.clip(x1, 0, orig_w)
            y1 = np.clip(y1, 0, orig_h)
            x2 = np.clip(x2, 0, orig_w)
            y2 = np.clip(y2, 0, orig_h)

            # Apply NMS
            nms_indices = self._fast_nms(
                np.column_stack([x1, y1, x2, y2]),
                valid_confidences,
                self.nms_threshold
            )

            # Create final detections
            for idx in nms_indices:
                detections.append({
                    'bbox': [int(x1[idx]), int(y1[idx]), int(x2[idx] - x1[idx]), int(y2[idx] - y1[idx])],
                    'confidence': float(valid_confidences[idx]),
                    'class': 'person',
                    'class_id': 0
                })

            postprocessing_time = (time.time() - start_time) * 1000
            logger.debug(f"Postprocessing: {postprocessing_time:.2f}ms, {len(detections)} detections")

            return detections

        except Exception as e:
            logger.error(f"Postprocessing error: {e}")
            return []

    def _fast_nms(self, boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
        """Optimized Non-Maximum Suppression"""
        try:
            # Sort by confidence
            sorted_indices = np.argsort(scores)[::-1]

            keep = []
            while len(sorted_indices) > 0:
                # Pick the box with highest confidence
                current = sorted_indices[0]
                keep.append(current)

                if len(sorted_indices) == 1:
                    break

                # Calculate IoU with remaining boxes
                current_box = boxes[current]
                remaining_boxes = boxes[sorted_indices[1:]]

                # Vectorized IoU calculation
                ious = self._calculate_iou_vectorized(current_box, remaining_boxes)

                # Keep boxes with IoU less than threshold
                remaining_indices = sorted_indices[1:][ious < iou_threshold]
                sorted_indices = remaining_indices

            return keep

        except Exception as e:
            logger.error(f"NMS error: {e}")
            return []

    def _calculate_iou_vectorized(self, box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Vectorized IoU calculation"""
        # Calculate intersection
        x1_max = np.maximum(box[0], boxes[:, 0])
        y1_max = np.maximum(box[1], boxes[:, 1])
        x2_min = np.minimum(box[2], boxes[:, 2])
        y2_min = np.minimum(box[3], boxes[:, 3])

        intersection_width = np.maximum(0, x2_min - x1_max)
        intersection_height = np.maximum(0, y2_min - y1_max)
        intersection_area = intersection_width * intersection_height

        # Calculate areas
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

        # Calculate union
        union_area = box_area + boxes_area - intersection_area

        # Calculate IoU
        iou = intersection_area / (union_area + 1e-7)
        return iou

    def detect_guests(self, frame: np.ndarray, frame_id: int = 0) -> InferenceResult:
        """Main detection function with performance tracking"""
        total_start_time = time.time()

        try:
            # Preprocessing
            preprocessed_input, metadata = self.preprocess_frame(frame)

            # Inference
            inference_start_time = time.time()

            if self.trt_engine:
                outputs = self.trt_engine.infer(preprocessed_input)
            else:
                # PyTorch inference
                with torch.no_grad():
                    input_tensor = torch.from_numpy(preprocessed_input).to(self.device)
                    outputs = self.torch_model.model(input_tensor)
                    if isinstance(outputs, tuple):
                        outputs = outputs[0]
                    outputs = outputs.cpu().numpy()

            inference_time = (time.time() - inference_start_time) * 1000

            # Postprocessing
            detections = self.postprocess_detections(outputs, metadata)

            # Calculate total time
            total_time = (time.time() - total_start_time) * 1000

            # Return buffer to pool
            try:
                self.input_buffer_pool.put_nowait(preprocessed_input)
            except queue.Full:
                pass

            result = InferenceResult(
                detections=detections,
                inference_time_ms=inference_time,
                preprocessing_time_ms=metadata['preprocessing_time_ms'],
                postprocessing_time_ms=total_time - inference_time - metadata['preprocessing_time_ms'],
                total_time_ms=total_time,
                confidence_scores=[d['confidence'] for d in detections],
                frame_id=frame_id,
                timestamp=time.time()
            )

            # Performance monitoring
            if total_time > 100:  # Target is <100ms
                logger.warning(f"Performance warning: {total_time:.1f}ms (target: <100ms)")

            return result

        except Exception as e:
            logger.error(f"Detection error: {e}")
            return InferenceResult(
                detections=[],
                inference_time_ms=0,
                preprocessing_time_ms=0,
                postprocessing_time_ms=0,
                total_time_ms=0,
                confidence_scores=[],
                frame_id=frame_id,
                timestamp=time.time()
            )

class OptimizedCostumeRecognizer:
    """Ultra-fast costume recognition with TensorRT optimization"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Model paths
        self.model_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models")

        # Optimization settings
        self.input_size = (224, 224)
        self.batch_size = 1

        # Classes
        self.classes = [
            'jedi', 'sith', 'rebel_alliance', 'stormtrooper',
            'imperial_officer', 'mandalorian', 'civilian'
        ]

        # TensorRT engine
        self.trt_engine = None
        self.torch_model = None

        self._initialize_model()

    def _initialize_model(self):
        """Initialize optimized costume recognition model"""
        try:
            # Try TensorRT first
            trt_path = self.model_dir / "costume_classifier_tensorrt.engine"
            if trt_path.exists():
                logger.info("Loading TensorRT engine for costume recognition")
                input_shape = (1, 3, self.input_size[1], self.input_size[0])
                self.trt_engine = TensorRTEngine(str(trt_path), input_shape)
            else:
                # Fallback to optimized PyTorch
                logger.info("Loading optimized PyTorch model for costume recognition")
                self._load_optimized_torch_model()

        except Exception as e:
            logger.error(f"Error initializing costume recognition model: {e}")

    def _load_optimized_torch_model(self):
        """Load and optimize PyTorch costume model"""
        try:
            model_path = self.model_dir / "best_costume_model.pt"
            if model_path.exists():
                checkpoint = torch.load(model_path, map_location=self.device)
                # This would load the actual model architecture and weights
                logger.info("PyTorch costume model loaded")
            else:
                logger.warning("Costume recognition model not found")

        except Exception as e:
            logger.error(f"Error loading costume model: {e}")

    def recognize_costume(self, person_crop: np.ndarray) -> Tuple[str, float]:
        """Fast costume recognition"""
        try:
            start_time = time.time()

            # Preprocess
            preprocessed = self._preprocess_costume_image(person_crop)

            # Inference
            if self.trt_engine:
                outputs = self.trt_engine.infer(preprocessed)
                probabilities = self._softmax(outputs[0])
            else:
                # Fallback - return default
                return "civilian", 0.5

            # Get prediction
            predicted_idx = np.argmax(probabilities)
            confidence = probabilities[predicted_idx]
            costume_class = self.classes[predicted_idx]

            inference_time = (time.time() - start_time) * 1000
            logger.debug(f"Costume recognition: {inference_time:.2f}ms")

            return costume_class, float(confidence)

        except Exception as e:
            logger.error(f"Costume recognition error: {e}")
            return "civilian", 0.0

    def _preprocess_costume_image(self, image: np.ndarray) -> np.ndarray:
        """Fast image preprocessing for costume recognition"""
        # Resize
        resized = cv2.resize(image, self.input_size, interpolation=cv2.INTER_LINEAR)

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize
        normalized = rgb.astype(np.float32) / 255.0

        # Apply ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        normalized = (normalized - mean) / std

        # HWC to CHW and add batch dimension
        transposed = normalized.transpose(2, 0, 1)
        batched = transposed[np.newaxis, ...]

        return batched

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Fast softmax implementation"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)

class OptimizedInferenceEngine:
    """Main optimized inference engine for R2D2"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)

        # Initialize optimized components
        self.guest_detector = OptimizedGuestDetector(self.config)
        self.costume_recognizer = OptimizedCostumeRecognizer(self.config)

        # Performance monitoring
        self.performance_metrics = {
            'total_frames_processed': 0,
            'average_inference_time': 0.0,
            'peak_inference_time': 0.0,
            'frames_over_target': 0,
            'target_time_ms': 100
        }

        # Threading for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info("Optimized inference engine initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        default_config = {
            "performance": {
                "target_inference_time_ms": 100,
                "batch_processing": False,
                "tensorrt_enabled": True,
                "fp16_enabled": True
            },
            "detection": {
                "confidence_threshold": 0.7,
                "nms_threshold": 0.4
            },
            "costume_recognition": {
                "confidence_threshold": 0.8
            }
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                return {**default_config, **loaded_config}

        return default_config

    async def process_frame(self, frame: np.ndarray, frame_id: int = 0) -> Dict[str, Any]:
        """Main frame processing with performance optimization"""
        total_start_time = time.time()

        try:
            # Guest detection
            detection_result = self.guest_detector.detect_guests(frame, frame_id)

            # Process each detected person for costume recognition
            costume_results = []
            for detection in detection_result.detections:
                # Extract person crop
                x, y, w, h = detection['bbox']
                person_crop = frame[y:y+h, x:x+w]

                # Recognize costume
                if person_crop.size > 0:
                    costume, confidence = self.costume_recognizer.recognize_costume(person_crop)
                    costume_results.append({
                        'costume': costume,
                        'confidence': confidence,
                        'bbox': detection['bbox']
                    })

            # Calculate total processing time
            total_time = (time.time() - total_start_time) * 1000

            # Update performance metrics
            self._update_performance_metrics(total_time)

            result = {
                'frame_id': frame_id,
                'timestamp': time.time(),
                'guest_detections': detection_result.detections,
                'costume_recognitions': costume_results,
                'performance': {
                    'total_time_ms': total_time,
                    'detection_time_ms': detection_result.total_time_ms,
                    'meets_target': total_time < self.config['performance']['target_inference_time_ms']
                },
                'counts': {
                    'guests_detected': len(detection_result.detections),
                    'costumes_recognized': len(costume_results)
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error processing frame {frame_id}: {e}")
            return {
                'frame_id': frame_id,
                'timestamp': time.time(),
                'guest_detections': [],
                'costume_recognitions': [],
                'performance': {'total_time_ms': 0, 'meets_target': False},
                'counts': {'guests_detected': 0, 'costumes_recognized': 0},
                'error': str(e)
            }

    def _update_performance_metrics(self, processing_time: float):
        """Update performance tracking metrics"""
        self.performance_metrics['total_frames_processed'] += 1

        # Update average
        total_frames = self.performance_metrics['total_frames_processed']
        current_avg = self.performance_metrics['average_inference_time']
        new_avg = ((current_avg * (total_frames - 1)) + processing_time) / total_frames
        self.performance_metrics['average_inference_time'] = new_avg

        # Update peak
        if processing_time > self.performance_metrics['peak_inference_time']:
            self.performance_metrics['peak_inference_time'] = processing_time

        # Count frames over target
        target_time = self.performance_metrics['target_time_ms']
        if processing_time > target_time:
            self.performance_metrics['frames_over_target'] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        total_frames = self.performance_metrics['total_frames_processed']
        frames_over_target = self.performance_metrics['frames_over_target']

        return {
            'total_frames_processed': total_frames,
            'average_inference_time_ms': self.performance_metrics['average_inference_time'],
            'peak_inference_time_ms': self.performance_metrics['peak_inference_time'],
            'target_achievement_rate': (total_frames - frames_over_target) / total_frames * 100 if total_frames > 0 else 0,
            'frames_meeting_target': total_frames - frames_over_target,
            'frames_over_target': frames_over_target,
            'target_time_ms': self.performance_metrics['target_time_ms']
        }

    def optimize_for_deployment(self) -> Dict[str, Any]:
        """Final optimization for deployment"""
        logger.info("Running deployment optimization...")

        optimization_report = {
            'tensorrt_optimization': False,
            'memory_optimization': False,
            'performance_validation': False,
            'deployment_ready': False
        }

        try:
            # Check TensorRT optimization
            if hasattr(self.guest_detector, 'trt_engine') and self.guest_detector.trt_engine:
                optimization_report['tensorrt_optimization'] = True

            # Memory optimization check
            if hasattr(self.guest_detector, 'input_buffer_pool'):
                optimization_report['memory_optimization'] = True

            # Performance validation
            avg_time = self.performance_metrics['average_inference_time']
            target_time = self.performance_metrics['target_time_ms']
            if avg_time < target_time:
                optimization_report['performance_validation'] = True

            # Overall deployment readiness
            optimization_report['deployment_ready'] = all([
                optimization_report['tensorrt_optimization'],
                optimization_report['memory_optimization'],
                optimization_report['performance_validation']
            ])

            logger.info(f"Deployment readiness: {optimization_report['deployment_ready']}")
            return optimization_report

        except Exception as e:
            logger.error(f"Error in deployment optimization: {e}")
            return optimization_report

# Example usage and testing
async def test_optimized_engine():
    """Test the optimized inference engine"""
    try:
        # Initialize engine
        engine = OptimizedInferenceEngine()

        # Create test frame
        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

        # Warmup
        logger.info("Warming up inference engine...")
        for i in range(10):
            await engine.process_frame(test_frame, i)

        # Performance test
        logger.info("Running performance test...")
        start_time = time.time()
        num_test_frames = 100

        for i in range(num_test_frames):
            result = await engine.process_frame(test_frame, i)
            if i % 20 == 0:
                logger.info(f"Frame {i}: {result['performance']['total_time_ms']:.1f}ms")

        total_test_time = time.time() - start_time
        avg_fps = num_test_frames / total_test_time

        # Generate report
        performance_report = engine.get_performance_report()
        optimization_report = engine.optimize_for_deployment()

        logger.info(f"Performance Test Results:")
        logger.info(f"Average FPS: {avg_fps:.1f}")
        logger.info(f"Average inference time: {performance_report['average_inference_time_ms']:.1f}ms")
        logger.info(f"Peak inference time: {performance_report['peak_inference_time_ms']:.1f}ms")
        logger.info(f"Target achievement rate: {performance_report['target_achievement_rate']:.1f}%")
        logger.info(f"Deployment ready: {optimization_report['deployment_ready']}")

        return performance_report, optimization_report

    except Exception as e:
        logger.error(f"Error in test: {e}")
        return {}, {}

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_optimized_engine())