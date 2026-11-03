"""A normalized, simple lot polygon; vehicles are selected by bottom-center."""
import json
import math
from pathlib import Path
import cv2
import numpy as np


def validate_polygon(points):
    if not isinstance(points, list) or len(points) < 3:
        raise ValueError('ROI polygon needs at least three [x,y] points')
    for p in points:
        if not isinstance(p, list) or len(p) != 2 or any(
            type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in p
        ):
            raise ValueError('ROI coordinates must be finite numbers between 0 and 1')
    if len(set(map(tuple, points))) != len(points):
        raise ValueError('ROI vertices must be distinct; do not repeat the first point')

    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    def on_segment(a, b, p):
        return abs(cross(a,b,p)) < 1e-10 and all(
            min(a[k],b[k])-1e-10 <= p[k] <= max(a[k],b[k])+1e-10 for k in (0,1))

    def intersects(a,b,c,d):
        return (cross(a,b,c)*cross(a,b,d) < 0 and cross(c,d,a)*cross(c,d,b) < 0
                or on_segment(a,b,c) or on_segment(a,b,d)
                or on_segment(c,d,a) or on_segment(c,d,b))

    n = len(points)
    for i in range(n):
        for j in range(i+1,n):
            if j == i+1 or (i == 0 and j == n-1):
                continue
            if intersects(points[i],points[(i+1)%n],points[j],points[(j+1)%n]):
                raise ValueError('ROI edges must not cross or touch other nonadjacent edges')
    area = abs(sum(points[i][0]*points[(i+1)%n][1] - points[(i+1)%n][0]*points[i][1]
                   for i in range(n))) / 2
    if area < 1e-8:
        raise ValueError('ROI polygon has zero or negligible area')
    return np.asarray(points, dtype=np.float32)


class LotROI:
    def __init__(self, points):
        self.points = validate_polygon(points)

    @classmethod
    def load(cls, path):
        config = json.loads(Path(path).read_text())
        if not isinstance(config, dict) or set(config) != {'polygon'}:
            raise ValueError('ROI config must contain only a polygon field')
        return cls(config['polygon'])

    def polygon(self, shape):
        height, width = shape[:2]
        if height < 2 or width < 2:
            raise ValueError('Image is too small for a lot ROI')
        return self.points * np.asarray([width-1, height-1], dtype=np.float32)

    def contains(self, detection, shape):
        x,y,w,h = detection['box_xywh']
        height,width = shape[:2]
        anchor = (float(min(width-1,max(0,x+w/2))), float(min(height-1,max(0,y+h))))
        return cv2.pointPolygonTest(self.polygon(shape), anchor, False) >= 0


def annotate(frame, detections, roi=None):
    """Return counted boxes and an audit image; excluded boxes stay visible in gray."""
    image = frame.copy()
    if roi is not None:
        cv2.polylines(image, [np.rint(roi.polygon(frame.shape)).astype(np.int32)], True, (255,180,0), 2)
    counted = []
    for detection in detections:
        inside = roi is None or roi.contains(detection, frame.shape)
        item = dict(detection)
        if inside:
            item['number'] = len(counted)+1
            counted.append(item)
        x,y,w,h = item['box_xywh']
        color = (0,220,0) if inside else (140,140,140)
        label = f"#{item['number']} {item['class']} {item['confidence']:.2f}" if inside else 'outside ROI'
        cv2.rectangle(image,(x,y),(x+w,y+h),color,2)
        cv2.circle(image,(min(frame.shape[1]-1,round(x+w/2)),min(frame.shape[0]-1,y+h)),3,color,-1)
        cv2.putText(image,label,(x,max(16,y-5)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,1)
    return counted,image
