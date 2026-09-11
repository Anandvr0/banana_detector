"""
Banana Curvature Detector — Phase 1: YOLO Segmentation Test
Runs a pretrained YOLO26 segmentation model on an image and prints all
detected objects with their class names and confidence scores.
Saves an annotated output image with segmentation masks and labels.
"""

import sys
import os
from pathlib import Path
from ultralytics import YOLO


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_NAME = "yolo26n-seg.pt"  # YOLO26 nano segmentation (COCO pretrained)
BANANA_CLASS_NAME = "banana"
OUTPUT_DIR = Path(__file__).parent / "output"


def verify_banana_class(model: YOLO) -> int | None:
    """Check that the loaded model knows the 'banana' class.
    Returns the class index if found, or None.
    """
    for idx, name in model.names.items():
        if name.lower() == BANANA_CLASS_NAME:
            return idx
    return None


def run_detection(image_path: str) -> None:
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    # Load model (downloads automatically on first run)
    print(f"Loading model: {MODEL_NAME}")
    model = YOLO(MODEL_NAME)

    # --- Requirement #9: verify banana class exists -------------------------
    banana_idx = verify_banana_class(model)
    if banana_idx is None:
        print("\n!!! PROBLEM !!!")
        print(f"The pretrained model '{MODEL_NAME}' does NOT contain a 'banana' class.")
        print("Available classes:")
        for idx, name in sorted(model.names.items()):
            print(f"  {idx}: {name}")
        sys.exit(1)
    print(f"✓ Banana class confirmed (index {banana_idx})")

    # --- Run segmentation inference -----------------------------------------
    print(f"\nRunning segmentation on: {image_path}")
    results = model(str(image_path), task="segment")

    # --- Print results ------------------------------------------------------
    result = results[0]
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        print("\nNo objects detected in this image.")
    else:
        print(f"\n{'='*50}")
        print(f"  Detected {len(boxes)} object(s)")
        print(f"{'='*50}")
        banana_count = 0
        for i, box in enumerate(boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls_id]
            is_banana = " ← BANANA!" if class_name.lower() == BANANA_CLASS_NAME else ""
            print(f"  [{i+1}] {class_name:>15s}  confidence: {conf:.4f}{is_banana}")
            if class_name.lower() == BANANA_CLASS_NAME:
                banana_count += 1
        print(f"{'='*50}")
        print(f"  Bananas found: {banana_count}")
        print(f"{'='*50}")

    # --- Save annotated output image ----------------------------------------
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_name = f"result_{image_path.stem}.jpg"
    out_path = OUTPUT_DIR / out_name

    annotated = result.plot()  # numpy array with masks + labels drawn
    import cv2
    cv2.imwrite(str(out_path), annotated)
    print(f"\nAnnotated image saved → {out_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect_banana.py <image_path> [image_path2 ...]")
        print("\nExamples:")
        print("  python detect_banana.py banana.jpg")
        print("  python detect_banana.py img1.jpg img2.png img3.webp")
        sys.exit(0)

    for img in sys.argv[1:]:
        print(f"\n{'─'*60}")
        run_detection(img)
        print(f"{'─'*60}")
