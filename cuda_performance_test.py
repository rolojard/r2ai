#!/usr/bin/env python3
"""
CUDA Performance Test for R2-D2 Video Processing
Tests PyTorch 2.5.0a0+872d972e41.nv24.08 performance on Orin Nano
"""

import torch
import time
import cv2
import numpy as np

def test_cuda_availability():
    """Test CUDA availability and device info"""
    print("=== CUDA Availability Test ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA capability: {torch.cuda.get_device_capability(0)}")
        print(f"Total memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print()

def test_matrix_operations():
    """Test basic CUDA matrix operations"""
    print("=== CUDA Matrix Operations Test ===")
    if not torch.cuda.is_available():
        print("CUDA not available, skipping GPU tests")
        return

    device = torch.device('cuda')

    # Test different matrix sizes relevant to video processing
    sizes = [512, 1024, 2048]

    for size in sizes:
        print(f"Testing {size}x{size} matrix operations...")

        # Create test matrices
        x = torch.randn(size, size, device=device)
        y = torch.randn(size, size, device=device)

        # Warm up
        for _ in range(10):
            _ = torch.matmul(x, y)
        torch.cuda.synchronize()

        # Time the operations
        start = time.time()
        for _ in range(50):
            z = torch.matmul(x, y)
        torch.cuda.synchronize()
        end = time.time()

        total_time = (end - start) * 1000
        per_op = total_time / 50
        print(f"  Matrix multiply: {per_op:.2f}ms per operation")

        # Memory usage
        allocated = torch.cuda.memory_allocated() / 1024**2
        cached = torch.cuda.memory_reserved() / 1024**2
        print(f"  GPU Memory - Allocated: {allocated:.1f}MB, Cached: {cached:.1f}MB")

        # Cleanup
        del x, y, z
        torch.cuda.empty_cache()
    print()

def test_conv_operations():
    """Test convolution operations for computer vision"""
    print("=== CUDA Convolution Operations Test ===")
    if not torch.cuda.is_available():
        print("CUDA not available, skipping GPU tests")
        return

    device = torch.device('cuda')

    # Test typical video processing dimensions
    batch_size = 1
    channels = 3
    height, width = 640, 480  # Common R2-D2 camera resolution

    print(f"Testing convolution on {batch_size}x{channels}x{height}x{width} tensors...")

    # Create test data
    input_tensor = torch.randn(batch_size, channels, height, width, device=device)
    conv_layer = torch.nn.Conv2d(channels, 32, kernel_size=3, padding=1).to(device)

    # Warm up
    for _ in range(10):
        _ = conv_layer(input_tensor)
    torch.cuda.synchronize()

    # Time the operations
    start = time.time()
    for _ in range(100):
        output = conv_layer(input_tensor)
    torch.cuda.synchronize()
    end = time.time()

    total_time = (end - start) * 1000
    per_op = total_time / 100
    fps_equivalent = 1000 / per_op

    print(f"  Convolution: {per_op:.2f}ms per operation")
    print(f"  Equivalent FPS: {fps_equivalent:.1f} fps")

    # Memory usage
    allocated = torch.cuda.memory_allocated() / 1024**2
    cached = torch.cuda.memory_reserved() / 1024**2
    print(f"  GPU Memory - Allocated: {allocated:.1f}MB, Cached: {cached:.1f}MB")

    print()

def test_video_processing_pipeline():
    """Test a complete video processing pipeline"""
    print("=== Video Processing Pipeline Test ===")
    if not torch.cuda.is_available():
        print("CUDA not available, skipping GPU tests")
        return

    device = torch.device('cuda')

    # Simulate R2-D2 video processing pipeline
    print("Simulating R2-D2 computer vision pipeline...")

    # Create synthetic video frame
    height, width = 640, 480
    frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

    # Convert to tensor and move to GPU
    start_total = time.time()

    # Step 1: Convert to tensor
    start = time.time()
    tensor = torch.from_numpy(frame).permute(2, 0, 1).float().unsqueeze(0).to(device) / 255.0
    torch.cuda.synchronize()
    tensor_time = (time.time() - start) * 1000

    # Step 2: Preprocessing (resize, normalize)
    start = time.time()
    resized = torch.nn.functional.interpolate(tensor, size=(224, 224), mode='bilinear')
    normalized = (resized - 0.5) / 0.5
    torch.cuda.synchronize()
    preprocess_time = (time.time() - start) * 1000

    # Step 3: Feature extraction (simulated CNN)
    start = time.time()
    conv1 = torch.nn.Conv2d(3, 32, 3, padding=1).to(device)
    conv2 = torch.nn.Conv2d(32, 64, 3, padding=1).to(device)
    pool = torch.nn.MaxPool2d(2)

    x = torch.relu(conv1(normalized))
    x = pool(x)
    x = torch.relu(conv2(x))
    x = pool(x)
    torch.cuda.synchronize()
    feature_time = (time.time() - start) * 1000

    # Step 4: Output processing
    start = time.time()
    features = torch.mean(x, dim=(2, 3))  # Global average pooling
    torch.cuda.synchronize()
    output_time = (time.time() - start) * 1000

    total_time = (time.time() - start_total) * 1000
    fps = 1000 / total_time

    print(f"  Tensor conversion: {tensor_time:.2f}ms")
    print(f"  Preprocessing: {preprocess_time:.2f}ms")
    print(f"  Feature extraction: {feature_time:.2f}ms")
    print(f"  Output processing: {output_time:.2f}ms")
    print(f"  Total pipeline: {total_time:.2f}ms")
    print(f"  Estimated FPS: {fps:.1f} fps")

    # Memory usage
    allocated = torch.cuda.memory_allocated() / 1024**2
    cached = torch.cuda.memory_reserved() / 1024**2
    print(f"  GPU Memory - Allocated: {allocated:.1f}MB, Cached: {cached:.1f}MB")

    print()

def test_memory_bandwidth():
    """Test GPU memory bandwidth"""
    print("=== GPU Memory Bandwidth Test ===")
    if not torch.cuda.is_available():
        print("CUDA not available, skipping GPU tests")
        return

    device = torch.device('cuda')

    # Test different data sizes
    sizes_mb = [10, 50, 100, 200]

    for size_mb in sizes_mb:
        elements = (size_mb * 1024 * 1024) // 4  # 4 bytes per float32

        print(f"Testing {size_mb}MB transfer...")

        # Host to device transfer
        host_data = torch.randn(elements)
        start = time.time()
        device_data = host_data.to(device)
        torch.cuda.synchronize()
        h2d_time = time.time() - start

        # Device to host transfer
        start = time.time()
        host_result = device_data.to('cpu')
        torch.cuda.synchronize()
        d2h_time = time.time() - start

        h2d_bandwidth = size_mb / h2d_time
        d2h_bandwidth = size_mb / d2h_time

        print(f"  Host->Device: {h2d_bandwidth:.1f} MB/s")
        print(f"  Device->Host: {d2h_bandwidth:.1f} MB/s")

        del host_data, device_data, host_result
        torch.cuda.empty_cache()

    print()

if __name__ == "__main__":
    print("NVIDIA Orin Nano CUDA Performance Test for R2-D2")
    print("=" * 50)
    print()

    test_cuda_availability()
    test_matrix_operations()
    test_conv_operations()
    test_video_processing_pipeline()
    test_memory_bandwidth()

    print("Performance test completed!")
    print("\nRecommendations for R2-D2:")
    print("- Use tensor operations on GPU for computer vision")
    print("- Batch process multiple frames when possible")
    print("- Keep working data on GPU to avoid transfer overhead")
    print("- Monitor GPU memory usage during extended operation")