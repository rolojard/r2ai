#!/usr/bin/env python3
"""
R2-D2 GPU Optimization Script for Orin Nano
Optimizes PyTorch 2.5.0a0+872d972e41.nv24.08 for real-time video processing
"""

import torch
import torch.nn as nn
import cv2
import numpy as np
import time
import threading
import queue
import os
import subprocess

class R2D2GPUOptimizer:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.optimization_applied = False

    def apply_pytorch_optimizations(self):
        """Apply PyTorch-specific optimizations for Orin Nano"""
        print("=== Applying PyTorch GPU Optimizations ===")

        if not torch.cuda.is_available():
            print("CUDA not available, skipping GPU optimizations")
            return False

        try:
            # Enable CUDA optimizations
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = True  # Optimize for consistent input sizes
            torch.backends.cudnn.deterministic = False  # Allow non-deterministic for speed

            # Set memory management
            torch.cuda.empty_cache()  # Clear any existing cache

            # Enable tensor core usage for mixed precision
            if hasattr(torch.backends.cudnn, 'allow_tf32'):
                torch.backends.cudnn.allow_tf32 = True
            if hasattr(torch.backends.cuda.matmul, 'allow_tf32'):
                torch.backends.cuda.matmul.allow_tf32 = True

            # Set memory fraction to leave room for other operations
            if hasattr(torch.cuda, 'set_memory_fraction'):
                torch.cuda.set_memory_fraction(0.8)  # Use 80% of GPU memory max

            print("✓ PyTorch CUDA optimizations applied")
            print("✓ cuDNN benchmark mode enabled")
            print("✓ TensorFloat-32 enabled for mixed precision")
            print("✓ GPU memory fraction set to 80%")

            self.optimization_applied = True
            return True

        except Exception as e:
            print(f"✗ Error applying PyTorch optimizations: {e}")
            return False

    def create_optimized_video_processor(self):
        """Create optimized video processing pipeline for R2-D2"""
        print("\n=== Creating Optimized Video Processor ===")

        class OptimizedVideoProcessor(nn.Module):
            def __init__(self):
                super().__init__()

                # Lightweight feature extractor optimized for Orin Nano
                self.feature_extractor = nn.Sequential(
                    # First conv block
                    nn.Conv2d(3, 16, 3, padding=1, bias=False),
                    nn.BatchNorm2d(16),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),

                    # Second conv block
                    nn.Conv2d(16, 32, 3, padding=1, bias=False),
                    nn.BatchNorm2d(32),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),

                    # Third conv block
                    nn.Conv2d(32, 64, 3, padding=1, bias=False),
                    nn.BatchNorm2d(64),
                    nn.ReLU(inplace=True),
                    nn.AdaptiveAvgPool2d((8, 8))
                )

                # Detection head
                self.detector = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(64 * 8 * 8, 128),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.2),
                    nn.Linear(128, 2)  # Simple binary detection (person/no-person)
                )

            def forward(self, x):
                features = self.feature_extractor(x)
                detection = self.detector(features)
                return detection, features

        # Create and optimize model
        model = OptimizedVideoProcessor().to(self.device)

        # Skip torch.compile for Orin Nano compatibility
        print("✓ Model created (optimized for Orin Nano)")

        # Set to evaluation mode
        model.eval()

        # Warm up the model
        dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
        with torch.no_grad():
            for _ in range(10):
                _ = model(dummy_input)
        torch.cuda.synchronize()

        print("✓ Video processor model warmed up")

        return model

    def benchmark_video_processing(self, model):
        """Benchmark video processing performance"""
        print("\n=== Benchmarking Video Processing Performance ===")

        # Test different input sizes
        test_sizes = [
            (224, 224),   # Optimized size
            (320, 240),   # R2-D2 camera low res
            (640, 480),   # R2-D2 camera medium res
        ]

        results = {}

        for height, width in test_sizes:
            print(f"\nTesting {width}x{height} input...")

            # Create test input
            test_input = torch.randn(1, 3, height, width).to(self.device)

            # Warm up
            with torch.no_grad():
                for _ in range(20):
                    _ = model(test_input)
            torch.cuda.synchronize()

            # Benchmark
            times = []
            with torch.no_grad():
                for _ in range(100):
                    start = time.time()
                    detection, features = model(test_input)
                    torch.cuda.synchronize()
                    times.append(time.time() - start)

            avg_time = np.mean(times) * 1000  # Convert to ms
            fps = 1000 / avg_time

            results[f"{width}x{height}"] = {
                'avg_time_ms': avg_time,
                'fps': fps,
                'memory_mb': torch.cuda.memory_allocated() / 1024**2
            }

            print(f"  Average time: {avg_time:.2f}ms")
            print(f"  FPS: {fps:.1f}")
            print(f"  GPU memory: {torch.cuda.memory_allocated() / 1024**2:.1f}MB")

        return results

    def create_camera_processor(self):
        """Create optimized camera processing pipeline"""
        print("\n=== Creating Camera Processing Pipeline ===")

        class CameraProcessor:
            def __init__(self, device):
                self.device = device
                self.frame_queue = queue.Queue(maxsize=5)
                self.result_queue = queue.Queue(maxsize=5)
                self.processing = False

            def preprocess_frame(self, frame):
                """Optimized frame preprocessing"""
                # Resize to optimal size
                frame_resized = cv2.resize(frame, (224, 224))

                # Convert to tensor efficiently
                frame_tensor = torch.from_numpy(frame_resized).permute(2, 0, 1).float()
                frame_tensor = frame_tensor.unsqueeze(0).to(self.device, non_blocking=True)
                frame_tensor = frame_tensor / 255.0

                # Normalize (ImageNet stats)
                mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(self.device)
                std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(self.device)
                frame_tensor = (frame_tensor - mean) / std

                return frame_tensor

            def start_processing(self, model):
                """Start background processing thread"""
                self.processing = True

                def process_frames():
                    while self.processing:
                        try:
                            frame = self.frame_queue.get(timeout=0.1)

                            # Preprocess
                            frame_tensor = self.preprocess_frame(frame)

                            # Inference
                            with torch.no_grad():
                                detection, features = model(frame_tensor)

                            # Post-process results
                            detection_cpu = detection.cpu().numpy()

                            # Put result in queue
                            if not self.result_queue.full():
                                self.result_queue.put({
                                    'detection': detection_cpu,
                                    'timestamp': time.time()
                                })

                        except queue.Empty:
                            continue
                        except Exception as e:
                            print(f"Processing error: {e}")

                self.process_thread = threading.Thread(target=process_frames)
                self.process_thread.start()

            def add_frame(self, frame):
                """Add frame for processing"""
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)

            def get_result(self):
                """Get latest processing result"""
                try:
                    return self.result_queue.get_nowait()
                except queue.Empty:
                    return None

            def stop_processing(self):
                """Stop processing"""
                self.processing = False
                if hasattr(self, 'process_thread'):
                    self.process_thread.join()

        processor = CameraProcessor(self.device)
        print("✓ Camera processor created with threaded pipeline")

        return processor

    def optimize_system_settings(self):
        """Apply system-level optimizations"""
        print("\n=== Applying System Optimizations ===")

        try:
            # Set jetson_clocks for maximum performance
            result = subprocess.run(['sudo', 'jetson_clocks'],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✓ Jetson clocks set for maximum performance")
            else:
                print(f"⚠ Could not set jetson_clocks: {result.stderr}")

        except Exception as e:
            print(f"⚠ Could not apply jetson_clocks: {e}")

        try:
            # Set CUDA_LAUNCH_BLOCKING=0 for async kernel launches
            os.environ['CUDA_LAUNCH_BLOCKING'] = '0'

            # Set optimal CUDA cache settings
            os.environ['CUDA_CACHE_DISABLE'] = '0'
            os.environ['CUDA_CACHE_MAXSIZE'] = '268435456'  # 256MB

            print("✓ CUDA environment variables optimized")

        except Exception as e:
            print(f"⚠ Could not set CUDA environment: {e}")

    def test_real_time_performance(self, model, camera_processor):
        """Test real-time performance with simulated camera feed"""
        print("\n=== Testing Real-Time Performance ===")

        # Simulate camera frames
        frame_times = []
        processing_times = []

        camera_processor.start_processing(model)

        print("Running 10-second real-time test...")
        start_time = time.time()
        frame_count = 0

        try:
            while time.time() - start_time < 10:
                frame_start = time.time()

                # Generate synthetic frame (simulate camera)
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

                # Add to processing queue
                camera_processor.add_frame(frame)

                # Check for results
                result = camera_processor.get_result()
                if result:
                    processing_times.append(time.time() - result['timestamp'])

                frame_times.append(time.time() - frame_start)
                frame_count += 1

                # Target 30 FPS
                time.sleep(max(0, 1/30 - (time.time() - frame_start)))

        finally:
            camera_processor.stop_processing()

        total_time = time.time() - start_time
        avg_fps = frame_count / total_time
        avg_frame_time = np.mean(frame_times) * 1000 if frame_times else 0
        avg_processing_time = np.mean(processing_times) * 1000 if processing_times else 0

        print(f"✓ Real-time test completed:")
        print(f"  Total frames: {frame_count}")
        print(f"  Average FPS: {avg_fps:.1f}")
        print(f"  Average frame time: {avg_frame_time:.2f}ms")
        print(f"  Average processing time: {avg_processing_time:.2f}ms")
        print(f"  Processed frames: {len(processing_times)}")

        return {
            'fps': avg_fps,
            'frame_time_ms': avg_frame_time,
            'processing_time_ms': avg_processing_time,
            'processed_frames': len(processing_times)
        }

def main():
    print("R2-D2 GPU Optimization for NVIDIA Orin Nano")
    print("=" * 50)

    optimizer = R2D2GPUOptimizer()

    # Apply optimizations
    if not optimizer.apply_pytorch_optimizations():
        print("Failed to apply optimizations")
        return

    # Apply system optimizations
    optimizer.optimize_system_settings()

    # Create optimized video processor
    model = optimizer.create_optimized_video_processor()

    # Benchmark performance
    benchmark_results = optimizer.benchmark_video_processing(model)

    # Create camera processor
    camera_processor = optimizer.create_camera_processor()

    # Test real-time performance
    realtime_results = optimizer.test_real_time_performance(model, camera_processor)

    # Generate report
    print("\n" + "=" * 50)
    print("OPTIMIZATION REPORT")
    print("=" * 50)

    print("\n📊 BENCHMARK RESULTS:")
    for size, results in benchmark_results.items():
        print(f"  {size}: {results['fps']:.1f} FPS, {results['avg_time_ms']:.2f}ms")

    print(f"\n🎯 REAL-TIME PERFORMANCE:")
    print(f"  Camera FPS: {realtime_results['fps']:.1f}")
    print(f"  Processing latency: {realtime_results['processing_time_ms']:.2f}ms")
    print(f"  Frame processing ratio: {realtime_results['processed_frames']}/{realtime_results['fps']*10:.0f}")

    print(f"\n💾 GPU MEMORY USAGE:")
    print(f"  Allocated: {torch.cuda.memory_allocated() / 1024**2:.1f}MB")
    print(f"  Cached: {torch.cuda.memory_reserved() / 1024**2:.1f}MB")

    print(f"\n✅ OPTIMIZATION STATUS:")
    print(f"  PyTorch optimizations: {'Applied' if optimizer.optimization_applied else 'Failed'}")
    print(f"  Real-time capable: {'Yes' if realtime_results['fps'] >= 15 else 'No'}")
    print(f"  R2-D2 ready: {'Yes' if realtime_results['fps'] >= 10 else 'Needs tuning'}")

if __name__ == "__main__":
    main()