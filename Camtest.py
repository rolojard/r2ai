#!/usr/bin/env python3
"""
R2D2 Camera Test with YOLOv8 Object Detection
Optimized for PyTorch 2.5.0a0 and CUDA 12.6 on NVIDIA Orin Nano
"""

import cv2
import torch
from ultralytics import YOLO
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main camera testing function with YOLO detection"""
    try:
        # Check CUDA availability
        if torch.cuda.is_available():
            device = 'cuda'
            logger.info(f"CUDA available - using GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA Version: {torch.version.cuda}")
            logger.info(f"PyTorch Version: {torch.__version__}")
        else:
            device = 'cpu'
            logger.warning("CUDA not available - using CPU")

        # Load YOLO model with proper error handling
        logger.info("Loading YOLOv8 model...")
        try:
            model = YOLO('yolov8n.pt')
            model.to(device)
            logger.info(f"YOLO model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return 1

        # Initialize camera
        logger.info("Initializing camera...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            logger.error("Failed to open camera")
            return 1

        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Verify camera settings
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = cap.get(cv2.CAP_PROP_FPS)

        logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")

        # Performance monitoring
        frame_count = 0
        start_time = time.time()

        print('Press q to quit...')
        print('Press s to save current frame')
        print('Press i to show detection info')

        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                break

            frame_count += 1

            try:
                # Run YOLO detection
                results = model(frame, verbose=False, device=device)
                annotated_frame = results[0].plot()

                # Add performance info overlay
                if frame_count % 30 == 0:  # Update every 30 frames
                    elapsed_time = time.time() - start_time
                    fps = frame_count / elapsed_time

                    # Add FPS text to frame
                    cv2.putText(annotated_frame, f'FPS: {fps:.1f}', (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f'Device: {device.upper()}', (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Display frame
                cv2.imshow('R2D2 YOLO Detection', annotated_frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("Quit requested by user")
                    break
                elif key == ord('s'):
                    # Save current frame
                    timestamp = int(time.time())
                    filename = f'/home/rolo/r2ai/detected_frame_{timestamp}.jpg'
                    cv2.imwrite(filename, annotated_frame)
                    logger.info(f"Frame saved to {filename}")
                elif key == ord('i'):
                    # Show detection info
                    detections = results[0].boxes
                    if detections is not None and len(detections) > 0:
                        logger.info(f"Detected {len(detections)} objects:")
                        for i, detection in enumerate(detections):
                            conf = detection.conf.item()
                            cls = int(detection.cls.item())
                            class_name = model.names[cls]
                            logger.info(f"  {i+1}: {class_name} ({conf:.2f})")
                    else:
                        logger.info("No objects detected in current frame")

            except Exception as e:
                logger.error(f"Error during detection: {e}")
                # Continue with original frame if detection fails
                cv2.imshow('R2D2 YOLO Detection', frame)

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

        # Final statistics
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time
        logger.info(f"Session completed: {frame_count} frames in {total_time:.1f}s (avg {avg_fps:.1f} FPS)")

        return 0

    except Exception as e:
        logger.error(f"Camera test failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())