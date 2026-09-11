import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


MODEL_NAME = "yolo26n-seg.pt"
BANANA_CLASS_NAME = "banana"
OUTPUT_DIR = Path(__file__).parent / "output"


def calculate_curvature(mask):
    ys, xs = np.where(mask > 0)

    if len(xs) < 100:
        return None

    points = np.column_stack((xs, ys)).astype(np.float32)

    mean = points.mean(axis=0)
    centered = points - mean

    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    direction = vt[0]

    if direction[0] < 0:
        direction = -direction

    projection = centered @ direction
    perpendicular = centered @ np.array([-direction[1], direction[0]])

    min_projection = projection.min()
    max_projection = projection.max()

    length = max_projection - min_projection

    if length <= 0:
        return None

    bins = np.linspace(min_projection, max_projection, 100)
    centerline = []

    for i in range(len(bins) - 1):
        selected = perpendicular[
            (projection >= bins[i]) &
            (projection < bins[i + 1])
        ]

        if len(selected) > 0:
            centerline.append([
                (bins[i] + bins[i + 1]) / 2,
                np.median(selected)
            ])

    centerline = np.array(centerline)

    if len(centerline) < 5:
        return None

    x = centerline[:, 0]
    y = centerline[:, 1]

    start = np.array([x[0], y[0]])
    end = np.array([x[-1], y[-1]])

    line = end - start
    line_length = np.linalg.norm(line)

    if line_length <= 0:
        return None

    distances = np.abs(
        line[0] * (start[1] - y) -
        line[1] * (start[0] - x)
    ) / line_length

    max_deviation = distances.max()

    curvature_ratio = max_deviation / line_length

    score = min(100, curvature_ratio * 300)

    return score, max_deviation, line_length


def get_verdict(score):
    if score < 15:
        return "ALMOST STRAIGHT", "This banana is suspiciously committed to being straight."
    elif score < 35:
        return "SLIGHTLY CURVED", "A little bend. Nothing dramatic."
    elif score < 60:
        return "MODERATELY CURVED", "Okay, now we're getting somewhere."
    elif score < 80:
        return "VERY CURVED", "This banana has rejected the concept of straight lines."
    else:
        return "EXTREMELY CURVED", "This banana has become a mathematical problem."


def process_image(image_path, model):
    image_path = Path(image_path)

    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        return

    print(f"\nProcessing: {image_path}")

    results = model(str(image_path), task="segment")
    result = results[0]
    
    if result.boxes is None or len(result.boxes) == 0:
        print("Verdict: That's not a banana!")
        return

    banana_indices = []

    for i, box in enumerate(result.boxes):
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]

        if class_name.lower() == BANANA_CLASS_NAME:
            banana_indices.append(i)

    if not banana_indices:
        print("Verdict: That's not a banana!")
        return

    print(f"Bananas detected: {len(banana_indices)}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    for banana_number, index in enumerate(banana_indices, start=1):
        mask = result.masks.data[index].cpu().numpy()

        original_height, original_width = result.orig_shape

        mask = cv2.resize(
            mask,
            (original_width, original_height),
            interpolation=cv2.INTER_NEAREST
        )

        mask = (mask > 0.5).astype(np.uint8)

        calculation = calculate_curvature(mask)

        if calculation is None:
            print(f"Banana {banana_number}: Could not calculate curvature.")
            continue

        score, deviation, length = calculation
        verdict, message = get_verdict(score)

        confidence = float(result.boxes[index].conf[0])

        print(f"\nBanana {banana_number}")
        print(f"Confidence: {confidence:.2%}")
        print(f"Curvature score: {score:.1f}/100")
        print(f"Maximum deviation: {deviation:.1f} pixels")
        print(f"Banana length: {length:.1f} pixels")
        print(f"Classification: {verdict}")
        print(f"Verdict: {message}")

        annotated = cv2.cvtColor(
            cv2.imread(str(image_path)),
            cv2.COLOR_BGR2RGB
        )

        mask_uint8 = (mask * 255).astype(np.uint8)

        contours, _ = cv2.findContours(
            mask_uint8,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        cv2.drawContours(
            annotated,
            contours,
            -1,
            (0, 255, 0),
            3
        )

        annotated = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)

        text = f"Curvature: {score:.1f}/100"
        text2 = verdict

        cv2.putText(
            annotated,
            text,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            3
        )

        cv2.putText(
            annotated,
            text2,
            (30, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            3
        )

        out_name = f"curvature_{image_path.stem}_{banana_number}.jpg"
        out_path = OUTPUT_DIR / out_name

        cv2.imwrite(str(out_path), annotated)

        print(f"Result saved → {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python curvature.py <image_path>")
        print("\nExample:")
        print("  python curvature.py test_images/red_banana.jpeg")
        sys.exit(0)

    print(f"Loading model: {MODEL_NAME}")
    model = YOLO(MODEL_NAME)

    for image in sys.argv[1:]:
        process_image(image, model)