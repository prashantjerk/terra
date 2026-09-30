"""Empty-reference occupancy estimate, not semantic vehicle recognition."""
import cv2
import numpy as np


def validate_config(config):
    regions = config.get("regions", [])
    capacity = config.get("capacity")
    if not regions or type(capacity) is not int or capacity != len(regions):
        raise ValueError("Define exactly one region per parking space; capacity must equal the region count")
    ids = set()
    for region in regions:
        name = region.get("id")
        points = region.get("points", [])
        if not isinstance(name, str) or not name or name in ids:
            raise ValueError("Each region needs a unique nonempty id")
        ids.add(name)
        if len(points) < 3 or any(len(p) != 2 or any(
                not isinstance(v, (int, float)) or not np.isfinite(v) or not 0 <= v <= 1
                for v in p) for p in points):
            raise ValueError("Region points must be normalized [x,y] coordinates between 0 and 1")
        if not cv2.isContourConvex(np.array(points, dtype=np.float32)):
            raise ValueError("Region polygons must be convex with points ordered around their boundary")
    for key, default, low, high in [("pixel_threshold", 30, 1, 255),
                                    ("occupied_fraction", .15, .001, 1)]:
        value = config.get(key, default)
        if not isinstance(value, (int, float)) or not np.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid {key}")
    return config


class Detector:
    def __init__(self, reference, config):
        self.config = validate_config(config)
        self.shape = reference.shape
        self.reference = self.gray(reference)
        h, w = self.reference.shape
        self.regions = []
        for region in config["regions"]:
            polygon = np.rint(np.array(region["points"]) * [w - 1, h - 1]).astype(np.int32)
            mask = np.zeros((h, w), np.uint8)
            cv2.fillPoly(mask, [polygon], 255)
            if cv2.countNonZero(mask) < 25:
                raise ValueError("Region too small at capture resolution")
            self.regions.append((region["id"], polygon, mask))

    @staticmethod
    def gray(frame):
        return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)

    def analyze(self, frame):
        if frame.shape != self.shape:
            raise ValueError("Frame dimensions differ from reference; recapture reference using this camera resolution")
        diff = cv2.absdiff(self.reference, self.gray(frame))
        changed = (diff >= self.config.get("pixel_threshold", 30)).astype(np.uint8) * 255
        changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        annotated = frame.copy()
        results = []
        for name, polygon, mask in self.regions:
            fraction = cv2.countNonZero(cv2.bitwise_and(changed, mask)) / cv2.countNonZero(mask)
            occupied = fraction >= self.config.get("occupied_fraction", .15)
            results.append({"id": name, "occupied": occupied, "changed_fraction": round(fraction, 4)})
            color = (0, 0, 255) if occupied else (0, 200, 0)
            cv2.polylines(annotated, [polygon], True, color, 2)
            cv2.putText(annotated, f"{name}: {fraction:.2f}", tuple(polygon[0]),
                        cv2.FONT_HERSHEY_SIMPLEX, .4, color, 1)
        count = sum(r["occupied"] for r in results)
        return {"numOfCarsParked": count, "capacity": self.config["capacity"],
                "available": self.config["capacity"] - count, "regions": results}, annotated, changed
