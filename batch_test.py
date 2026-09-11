"""
Banana Curvature Detector — Phase 1: Batch Test Runner
Runs detect_banana.py on every image in test_images/ and produces
a summary table of detection results.
"""

import sys
import os
from pathlib import Path
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_NAME = "yolo26n-seg.pt"
BANANA_CLASS_NAME = "banana"
TEST_DIR = Path(__file__).parent / "test_images"
OUTPUT_DIR = Path(__file__).parent / "output"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def run_batch_test():
    # Collect images
    images = sorted(
        f for f in TEST_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not images:
        print(f"ERROR: No images found in {TEST_DIR}")
        print(f"Place banana images in: {TEST_DIR.resolve()}")
        print(f"Supported formats: {', '.join(IMAGE_EXTENSIONS)}")
        sys.exit(1)

    print(f"Found {len(images)} image(s) in {TEST_DIR}\n")

    # Load model
    print(f"Loading model: {MODEL_NAME}")
    model = YOLO(MODEL_NAME)

    # Verify banana class
    banana_idx = None
    for idx, name in model.names.items():
        if name.lower() == BANANA_CLASS_NAME:
            banana_idx = idx
            break
    if banana_idx is None:
        print(f"ERROR: Model does not contain '{BANANA_CLASS_NAME}' class!")
        sys.exit(1)
    print(f"✓ Banana class confirmed (index {banana_idx})\n")

    OUTPUT_DIR.mkdir(exist_ok=True)

    # ---------------------------------------------------------------------------
    # Run detection on each image and collect results
    # ---------------------------------------------------------------------------
    results_table = []

    for img_path in images:
        print(f"{'─'*60}")
        print(f"Processing: {img_path.name}")

        results = model(str(img_path), task="segment")
        result = results[0]
        boxes = result.boxes

        # Count bananas and gather confidences
        banana_count = 0
        banana_confidences = []
        other_objects = []
        has_mask = False

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names[cls_id]
                if class_name.lower() == BANANA_CLASS_NAME:
                    banana_count += 1
                    banana_confidences.append(conf)
                else:
                    other_objects.append((class_name, conf))

        # Check if segmentation masks exist
        if result.masks is not None and len(result.masks) > 0:
            has_mask = True

        # Print per-image details
        if banana_count > 0:
            conf_str = ", ".join(f"{c:.4f}" for c in banana_confidences)
            print(f"  ✅ Banana detected! Count: {banana_count}, Confidence: [{conf_str}]")
            print(f"  🎭 Segmentation mask: {'YES' if has_mask else 'NO'}")
        else:
            print(f"  ❌ No banana detected")

        if other_objects:
            other_str = ", ".join(f"{name}({conf:.2f})" for name, conf in other_objects)
            print(f"  📦 Other objects: {other_str}")

        # Save annotated image
        import cv2
        annotated = result.plot()
        out_path = OUTPUT_DIR / f"result_{img_path.stem}.jpg"
        cv2.imwrite(str(out_path), annotated)
        print(f"  💾 Saved: {out_path.name}")

        results_table.append({
            "filename": img_path.name,
            "banana_detected": banana_count > 0,
            "banana_count": banana_count,
            "confidences": banana_confidences,
            "has_mask": has_mask,
            "other_objects": other_objects,
        })

    # ---------------------------------------------------------------------------
    # Summary Table
    # ---------------------------------------------------------------------------
    print(f"\n{'═'*75}")
    print(f"  DETECTION SUMMARY — {len(images)} images tested")
    print(f"{'═'*75}")

    # Header
    print(f"  {'Filename':<35} {'Banana?':<10} {'Count':<7} {'Confidence':<20} {'Mask?':<6}")
    print(f"  {'─'*35} {'─'*10} {'─'*7} {'─'*20} {'─'*6}")

    detected_count = 0
    missed_count = 0

    for r in results_table:
        fname = r["filename"][:34]
        detected = "✅ YES" if r["banana_detected"] else "❌ NO"
        count = str(r["banana_count"])
        conf_str = ", ".join(f"{c:.2f}" for c in r["confidences"]) if r["confidences"] else "—"
        mask = "YES" if r["has_mask"] else "NO"

        print(f"  {fname:<35} {detected:<10} {count:<7} {conf_str:<20} {mask:<6}")

        if r["banana_detected"]:
            detected_count += 1
        else:
            missed_count += 1

    print(f"  {'─'*35} {'─'*10} {'─'*7} {'─'*20} {'─'*6}")
    print(f"\n  Total images:    {len(images)}")
    print(f"  Bananas found:   {detected_count}")
    print(f"  Bananas missed:  {missed_count}")

    if len(images) > 0:
        success_rate = (detected_count / len(images)) * 100
        print(f"  Success rate:    {success_rate:.1f}%")

    print(f"{'═'*75}")
    print(f"\n  Annotated images saved to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    run_batch_test()
