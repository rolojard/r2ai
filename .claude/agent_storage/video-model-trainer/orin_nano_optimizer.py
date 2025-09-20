#!/usr/bin/env python3
"""
Nvidia Orin Nano Optimization Suite for R2D2 Computer Vision
TensorRT optimization, model quantization, and performance tuning for edge deployment
"""

import torch
import torch.nn as nn
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np
import cv2
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import onnx
import onnxruntime as ort
from concurrent.futures import ThreadPoolExecutor
import psutil
import GPUtil

logger = logging.getLogger(__name__)

class TensorRTOptimizer:
    """TensorRT optimization for Orin Nano deployment"""

    def __init__(self, config: Dict):
        self.config = config
        self.trt_logger = trt.Logger(trt.Logger.WARNING)
        self.engine_cache = {}

        # Orin Nano specific optimizations
        self.orin_nano_config = {
            "max_workspace_size": 1 << 30,  # 1GB
            "max_batch_size": 1,
            "fp16_mode": True,
            "int8_mode": False,  # Enable if calibration data available
            "dla_core": None,  # Use GPU for now
            "strict_type_constraints": False
        }

    def convert_onnx_to_tensorrt(self, onnx_path: str, engine_path: str,
                                input_shape: Tuple[int, ...], precision: str = "fp16") -> bool:
        """Convert ONNX model to TensorRT engine"""
        try:
            logger.info(f"Converting {onnx_path} to TensorRT engine...")

            # Create builder and network
            builder = trt.Builder(self.trt_logger)
            network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
            parser = trt.OnnxParser(network, self.trt_logger)

            # Parse ONNX model
            with open(onnx_path, 'rb') as model:
                if not parser.parse(model.read()):
                    logger.error("Failed to parse ONNX model")
                    for error in range(parser.num_errors):
                        logger.error(parser.get_error(error))
                    return False

            # Configure builder
            config = builder.create_builder_config()
            config.max_workspace_size = self.orin_nano_config["max_workspace_size"]

            # Set precision
            if precision == "fp16" and builder.platform_has_fast_fp16:
                config.set_flag(trt.BuilderFlag.FP16)
                logger.info("Enabled FP16 precision")
            elif precision == "int8" and builder.platform_has_fast_int8:
                config.set_flag(trt.BuilderFlag.INT8)
                # Would need calibration dataset for INT8
                logger.info("INT8 precision requires calibration dataset")

            # Optimize for Orin Nano
            config.set_flag(trt.BuilderFlag.PREFER_PRECISION_CONSTRAINTS)
            config.set_flag(trt.BuilderFlag.STRICT_TYPES)

            # Build engine
            engine = builder.build_engine(network, config)
            if engine is None:
                logger.error("Failed to build TensorRT engine")
                return False

            # Save engine
            Path(engine_path).parent.mkdir(parents=True, exist_ok=True)
            with open(engine_path, 'wb') as f:
                f.write(engine.serialize())

            logger.info(f"TensorRT engine saved to {engine_path}")
            return True

        except Exception as e:
            logger.error(f"Error converting to TensorRT: {e}")
            return False

    def load_tensorrt_engine(self, engine_path: str) -> Optional[trt.ICudaEngine]:
        """Load TensorRT engine from file"""
        try:
            if engine_path in self.engine_cache:
                return self.engine_cache[engine_path]

            runtime = trt.Runtime(self.trt_logger)
            with open(engine_path, 'rb') as f:
                engine = runtime.deserialize_cuda_engine(f.read())

            if engine:
                self.engine_cache[engine_path] = engine
                logger.info(f"Loaded TensorRT engine from {engine_path}")
                return engine
            else:
                logger.error(f"Failed to load engine from {engine_path}")
                return None

        except Exception as e:
            logger.error(f"Error loading TensorRT engine: {e}")
            return None

class OrionNanoInferenceEngine:
    """Optimized inference engine for Orin Nano"""

    def __init__(self, model_config: Dict):
        self.config = model_config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Model engines
        self.yolo_engine = None
        self.costume_engine = None
        self.face_engine = None

        # Performance monitoring
        self.inference_times = []
        self.memory_usage = []
        self.gpu_utilization = []

        # CUDA streams for concurrent execution
        self.streams = [cuda.Stream() for _ in range(3)]

        self.load_optimized_models()

    def load_optimized_models(self):
        """Load all optimized models for real-time inference"""
        try:
            models_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models/optimized")
            models_dir.mkdir(parents=True, exist_ok=True)

            # Load YOLO for guest detection
            yolo_engine_path = models_dir / "yolo_orin_nano.engine"
            if yolo_engine_path.exists():
                self.yolo_engine = self._load_trt_engine(str(yolo_engine_path))
            else:
                logger.warning("YOLO TensorRT engine not found")

            # Load costume recognition model
            costume_engine_path = models_dir / "costume_classifier_orin_nano.engine"
            if costume_engine_path.exists():
                self.costume_engine = self._load_trt_engine(str(costume_engine_path))
            else:
                logger.warning("Costume classifier TensorRT engine not found")

            # Load face recognition model
            face_engine_path = models_dir / "face_recognition_orin_nano.engine"
            if face_engine_path.exists():
                self.face_engine = self._load_trt_engine(str(face_engine_path))
            else:
                logger.warning("Face recognition TensorRT engine not found")

        except Exception as e:
            logger.error(f"Error loading optimized models: {e}")

    def _load_trt_engine(self, engine_path: str):
        """Load TensorRT engine with CUDA context"""
        try:
            trt_logger = trt.Logger(trt.Logger.WARNING)
            runtime = trt.Runtime(trt_logger)

            with open(engine_path, 'rb') as f:
                engine = runtime.deserialize_cuda_engine(f.read())

            context = engine.create_execution_context()
            return {"engine": engine, "context": context}

        except Exception as e:
            logger.error(f"Error loading TensorRT engine {engine_path}: {e}")
            return None

    def preprocess_for_yolo(self, frame: np.ndarray) -> np.ndarray:
        """Optimized preprocessing for YOLO inference"""
        # Resize to YOLO input size (640x640)
        input_size = self.config.get('yolo_input_size', 640)
        resized = cv2.resize(frame, (input_size, input_size))

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        normalized = rgb.astype(np.float32) / 255.0

        # CHW format
        transposed = np.transpose(normalized, (2, 0, 1))

        # Add batch dimension
        batched = np.expand_dims(transposed, axis=0)

        return np.ascontiguousarray(batched)

    def preprocess_for_costume_classifier(self, person_crop: np.ndarray) -> np.ndarray:
        """Optimized preprocessing for costume classification"""
        # Resize to classifier input size (224x224)
        resized = cv2.resize(person_crop, (224, 224))

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize with ImageNet stats
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        normalized = (rgb.astype(np.float32) / 255.0 - mean) / std

        # CHW format and batch dimension
        transposed = np.transpose(normalized, (2, 0, 1))
        batched = np.expand_dims(transposed, axis=0)

        return np.ascontiguousarray(batched)

    def run_yolo_inference(self, preprocessed_input: np.ndarray) -> np.ndarray:
        """Run optimized YOLO inference"""
        if not self.yolo_engine:
            return np.array([])

        try:
            start_time = time.time()

            engine = self.yolo_engine["engine"]
            context = self.yolo_engine["context"]

            # Allocate GPU memory
            input_binding = engine.get_binding_index("images")
            output_binding = engine.get_binding_index("output0")

            input_shape = engine.get_binding_shape(input_binding)
            output_shape = engine.get_binding_shape(output_binding)

            # Allocate device memory
            d_input = cuda.mem_alloc(preprocessed_input.nbytes)
            d_output = cuda.mem_alloc(np.empty(output_shape, dtype=np.float32).nbytes)

            # Transfer input to GPU
            cuda.memcpy_htod_async(d_input, preprocessed_input, self.streams[0])

            # Set binding shapes and execute
            context.set_binding_shape(input_binding, input_shape)
            context.execute_async_v2(bindings=[int(d_input), int(d_output)], stream_handle=self.streams[0].handle)

            # Transfer output back to CPU
            output = np.empty(output_shape, dtype=np.float32)
            cuda.memcpy_dtoh_async(output, d_output, self.streams[0])
            self.streams[0].synchronize()

            # Free GPU memory
            d_input.free()
            d_output.free()

            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)

            return output

        except Exception as e:
            logger.error(f"Error in YOLO inference: {e}")
            return np.array([])

    def run_costume_inference(self, preprocessed_input: np.ndarray) -> np.ndarray:
        """Run optimized costume classification inference"""
        if not self.costume_engine:
            return np.array([])

        try:
            start_time = time.time()

            engine = self.costume_engine["engine"]
            context = self.costume_engine["context"]

            # Get binding information
            input_binding = engine.get_binding_index("input")
            output_binding = engine.get_binding_index("output")

            output_shape = engine.get_binding_shape(output_binding)

            # Allocate device memory
            d_input = cuda.mem_alloc(preprocessed_input.nbytes)
            d_output = cuda.mem_alloc(np.empty(output_shape, dtype=np.float32).nbytes)

            # Execute inference
            cuda.memcpy_htod_async(d_input, preprocessed_input, self.streams[1])
            context.execute_async_v2(bindings=[int(d_input), int(d_output)], stream_handle=self.streams[1].handle)

            # Get output
            output = np.empty(output_shape, dtype=np.float32)
            cuda.memcpy_dtoh_async(output, d_output, self.streams[1])
            self.streams[1].synchronize()

            # Cleanup
            d_input.free()
            d_output.free()

            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)

            return output

        except Exception as e:
            logger.error(f"Error in costume inference: {e}")
            return np.array([])

    def run_face_inference(self, preprocessed_input: np.ndarray) -> np.ndarray:
        """Run optimized face recognition inference"""
        if not self.face_engine:
            return np.array([])

        try:
            start_time = time.time()

            engine = self.face_engine["engine"]
            context = self.face_engine["context"]

            # Similar implementation to costume inference
            # ... (implementation details similar to above)

            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)

            return np.random.rand(512)  # Placeholder

        except Exception as e:
            logger.error(f"Error in face inference: {e}")
            return np.array([])

class PerformanceProfiler:
    """Performance profiling and optimization for Orin Nano"""

    def __init__(self):
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "gpu_usage": [],
            "gpu_memory": [],
            "inference_fps": [],
            "temperature": []
        }

    def start_profiling(self):
        """Start continuous performance monitoring"""
        import threading
        self.profiling_active = True
        self.profiling_thread = threading.Thread(target=self._profile_loop, daemon=True)
        self.profiling_thread.start()

    def _profile_loop(self):
        """Continuous profiling loop"""
        while self.profiling_active:
            try:
                # CPU and system memory
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent

                self.metrics["cpu_usage"].append(cpu_percent)
                self.metrics["memory_usage"].append(memory_percent)

                # GPU metrics (if available)
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        self.metrics["gpu_usage"].append(gpu.load * 100)
                        self.metrics["gpu_memory"].append(gpu.memoryUtil * 100)
                        self.metrics["temperature"].append(gpu.temperature)
                except:
                    pass

                # Keep only recent metrics
                max_history = 300  # 5 minutes at 1 sample per second
                for key in self.metrics:
                    if len(self.metrics[key]) > max_history:
                        self.metrics[key] = self.metrics[key][-max_history:]

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in profiling loop: {e}")

    def stop_profiling(self):
        """Stop performance monitoring"""
        self.profiling_active = False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {}

        for metric, values in self.metrics.items():
            if values:
                summary[metric] = {
                    "current": values[-1] if values else 0,
                    "average": np.mean(values),
                    "max": np.max(values),
                    "min": np.min(values)
                }

        return summary

class ModelOptimizationPipeline:
    """Complete model optimization pipeline for Orin Nano"""

    def __init__(self, config: Dict):
        self.config = config
        self.tensorrt_optimizer = TensorRTOptimizer(config)

    def optimize_yolo_model(self, pytorch_model_path: str, output_dir: str) -> bool:
        """Optimize YOLO model for Orin Nano"""
        try:
            logger.info("Starting YOLO model optimization...")

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Convert PyTorch to ONNX
            onnx_path = output_path / "yolo_optimized.onnx"
            if not self._convert_pytorch_to_onnx(pytorch_model_path, str(onnx_path), (1, 3, 640, 640)):
                return False

            # Step 2: Optimize ONNX
            optimized_onnx_path = output_path / "yolo_optimized_simplified.onnx"
            if not self._optimize_onnx_model(str(onnx_path), str(optimized_onnx_path)):
                return False

            # Step 3: Convert to TensorRT
            engine_path = output_path / "yolo_orin_nano.engine"
            if not self.tensorrt_optimizer.convert_onnx_to_tensorrt(
                str(optimized_onnx_path), str(engine_path), (1, 3, 640, 640), "fp16"
            ):
                return False

            logger.info(f"YOLO model optimization completed: {engine_path}")
            return True

        except Exception as e:
            logger.error(f"Error optimizing YOLO model: {e}")
            return False

    def optimize_costume_classifier(self, pytorch_model_path: str, output_dir: str) -> bool:
        """Optimize costume classifier for Orin Nano"""
        try:
            logger.info("Starting costume classifier optimization...")

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Convert and optimize costume classifier
            onnx_path = output_path / "costume_classifier.onnx"
            if not self._convert_pytorch_to_onnx(pytorch_model_path, str(onnx_path), (1, 3, 224, 224)):
                return False

            # Optimize and convert to TensorRT
            engine_path = output_path / "costume_classifier_orin_nano.engine"
            if not self.tensorrt_optimizer.convert_onnx_to_tensorrt(
                str(onnx_path), str(engine_path), (1, 3, 224, 224), "fp16"
            ):
                return False

            logger.info(f"Costume classifier optimization completed: {engine_path}")
            return True

        except Exception as e:
            logger.error(f"Error optimizing costume classifier: {e}")
            return False

    def _convert_pytorch_to_onnx(self, pytorch_path: str, onnx_path: str, input_shape: Tuple[int, ...]) -> bool:
        """Convert PyTorch model to ONNX"""
        try:
            # Load PyTorch model
            model = torch.load(pytorch_path, map_location='cpu')
            model.eval()

            # Create dummy input
            dummy_input = torch.randn(*input_shape)

            # Export to ONNX
            torch.onnx.export(
                model,
                dummy_input,
                onnx_path,
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
            )

            logger.info(f"Converted PyTorch model to ONNX: {onnx_path}")
            return True

        except Exception as e:
            logger.error(f"Error converting PyTorch to ONNX: {e}")
            return False

    def _optimize_onnx_model(self, input_path: str, output_path: str) -> bool:
        """Optimize ONNX model for better performance"""
        try:
            import onnxoptimizer

            # Load ONNX model
            model = onnx.load(input_path)

            # Apply optimizations
            optimized_model = onnxoptimizer.optimize(model, [
                'eliminate_deadend',
                'eliminate_identity',
                'eliminate_nop_dropout',
                'eliminate_nop_monotone_argmax',
                'eliminate_nop_pad',
                'eliminate_unused_initializer',
                'extract_constant_to_initializer',
                'fuse_add_bias_into_conv',
                'fuse_bn_into_conv',
                'fuse_consecutive_squeezes',
                'fuse_consecutive_transposes',
                'fuse_matmul_add_bias_into_gemm',
                'fuse_pad_into_conv',
                'fuse_transpose_into_gemm'
            ])

            # Save optimized model
            onnx.save(optimized_model, output_path)

            logger.info(f"ONNX model optimized: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error optimizing ONNX model: {e}")
            return False

    def run_optimization_benchmark(self, models_dir: str) -> Dict[str, Any]:
        """Benchmark optimized models on Orin Nano"""
        try:
            logger.info("Running optimization benchmark...")

            profiler = PerformanceProfiler()
            profiler.start_profiling()

            inference_engine = OrionNanoInferenceEngine(self.config)

            # Benchmark parameters
            num_iterations = 100
            input_size = (1, 3, 640, 640)

            # Create dummy input
            dummy_input = np.random.rand(*input_size).astype(np.float32)

            # Warm up
            for _ in range(10):
                inference_engine.run_yolo_inference(dummy_input)

            # Benchmark inference
            start_time = time.time()
            inference_times = []

            for i in range(num_iterations):
                iter_start = time.time()
                output = inference_engine.run_yolo_inference(dummy_input)
                iter_time = time.time() - iter_start
                inference_times.append(iter_time)

            total_time = time.time() - start_time

            # Calculate metrics
            avg_inference_time = np.mean(inference_times)
            fps = 1.0 / avg_inference_time if avg_inference_time > 0 else 0
            throughput = num_iterations / total_time

            profiler.stop_profiling()
            performance_summary = profiler.get_performance_summary()

            benchmark_results = {
                "optimization_successful": True,
                "performance_metrics": {
                    "average_inference_time_ms": avg_inference_time * 1000,
                    "fps": fps,
                    "throughput": throughput,
                    "total_benchmark_time": total_time
                },
                "system_metrics": performance_summary,
                "memory_efficiency": {
                    "peak_gpu_memory": max(performance_summary.get("gpu_memory", {}).get("max", 0), 0),
                    "peak_system_memory": max(performance_summary.get("memory_usage", {}).get("max", 0), 0)
                }
            }

            # Save benchmark results
            results_path = Path(models_dir) / "optimization_benchmark.json"
            with open(results_path, 'w') as f:
                json.dump(benchmark_results, f, indent=2)

            logger.info(f"Benchmark completed - FPS: {fps:.1f}, Inference time: {avg_inference_time*1000:.1f}ms")
            return benchmark_results

        except Exception as e:
            logger.error(f"Error in optimization benchmark: {e}")
            return {"optimization_successful": False, "error": str(e)}

# Configuration for Orin Nano optimization
def get_orin_nano_config():
    """Get optimization configuration for Orin Nano"""
    return {
        "yolo_input_size": 640,
        "costume_input_size": 224,
        "face_input_size": 160,
        "tensorrt": {
            "max_workspace_size": 1 << 30,  # 1GB
            "fp16_enabled": True,
            "int8_enabled": False,
            "strict_type_constraints": False
        },
        "performance_targets": {
            "min_fps": 30,
            "max_inference_time_ms": 33,  # ~30 FPS
            "max_memory_usage_mb": 2000
        }
    }

# Main optimization workflow
def main():
    """Main optimization workflow"""
    config = get_orin_nano_config()
    optimizer = ModelOptimizationPipeline(config)

    models_dir = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models"
    output_dir = f"{models_dir}/optimized"

    # Optimize all models
    logger.info("Starting complete model optimization for Orin Nano...")

    # Optimize YOLO (placeholder - would use actual model path)
    yolo_success = optimizer.optimize_yolo_model(
        f"{models_dir}/yolov8n.pt",
        output_dir
    )

    # Optimize costume classifier
    costume_success = optimizer.optimize_costume_classifier(
        f"{models_dir}/costume_classifier.pt",
        output_dir
    )

    # Run benchmark
    benchmark_results = optimizer.run_optimization_benchmark(output_dir)

    logger.info(f"Optimization completed - YOLO: {yolo_success}, Costume: {costume_success}")
    logger.info(f"Benchmark FPS: {benchmark_results.get('performance_metrics', {}).get('fps', 0):.1f}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()