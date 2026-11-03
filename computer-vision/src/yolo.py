"""YOLOv8 COCO ONNX inference with OpenCV DNN; no PyTorch on the Pi."""
from pathlib import Path
import cv2
import numpy as np

VEHICLES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}


def letterbox(frame, size):
    if frame is None or frame.ndim != 3 or frame.shape[2] != 3 or min(frame.shape[:2]) < 2:
        raise ValueError('Expected a nonempty BGR image')
    height,width = frame.shape[:2]
    scale = min(size/width,size/height)
    rw,rh = max(1,round(width*scale)),max(1,round(height*scale))
    left,top = (size-rw)//2,(size-rh)//2
    canvas = np.full((size,size,3),114,dtype=np.uint8)
    canvas[top:top+rh,left:left+rw] = cv2.resize(frame,(rw,rh))
    return canvas,scale,left,top


def decode(output, shape, scale, left, top, confidence, iou, classes):
    values = np.asarray(output)
    if values.ndim != 3 or values.shape[0] != 1:
        raise ValueError('Expected raw YOLOv8 COCO output [1,84,N]; export with nms=False')
    if values.shape[1] == 84:
        rows = values[0].T
    elif values.shape[2] == 84:
        rows = values[0]
    else:
        raise ValueError('Only raw 80-class COCO YOLOv8 detection exports are supported')
    height,width = shape[:2]
    boxes,scores,names = [],[],[]
    for row in rows:
        if not np.isfinite(row).all():
            continue
        category = int(np.argmax(row[4:]))
        score = float(row[4+category])
        if category not in classes or not confidence <= score <= 1:
            continue
        cx,cy,bw,bh = map(float,row[:4])
        if bw <= 0 or bh <= 0:
            continue
        x1 = max(0,min(width,int(np.floor((cx-bw/2-left)/scale))))
        y1 = max(0,min(height,int(np.floor((cy-bh/2-top)/scale))))
        x2 = max(0,min(width,int(np.ceil((cx+bw/2-left)/scale))))
        y2 = max(0,min(height,int(np.ceil((cy+bh/2-top)/scale))))
        if x2 <= x1 or y2 <= y1:
            continue
        boxes.append([x1,y1,x2-x1,y2-y1])
        scores.append(score)
        names.append(VEHICLES[category])
    # Class-agnostic suppression avoids counting one vehicle as both car and truck.
    indices = np.asarray(cv2.dnn.NMSBoxes(boxes,scores,confidence,iou)).reshape(-1)
    return [{'number':n,'class':names[int(i)],'confidence':round(scores[int(i)],4),
             'box_xywh':boxes[int(i)]} for n,i in enumerate(indices,start=1)]


class YoloDetector:
    def __init__(self, model, confidence=.5, size=640, iou=.45, classes=(2,5,7)):
        if not 0 < confidence < 1 or not 0 < iou < 1:
            raise ValueError('Confidence and IoU must be between 0 and 1')
        if type(size) is not int or not 32 <= size <= 1280 or size % 32:
            raise ValueError('YOLO image size must be a multiple of 32 between 32 and 1280')
        if not classes or any(type(c) is not int or c not in VEHICLES for c in classes):
            raise ValueError('Vehicle classes must be chosen from 2,3,5,7 (COCO IDs)')
        if not model or not Path(model).is_file():
            raise ValueError('Supply --model pointing to a YOLOv8 COCO ONNX file; see YOLO_ROI.md')
        self.net = cv2.dnn.readNetFromONNX(str(model))
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.confidence,self.size,self.iou,self.classes = confidence,size,iou,tuple(classes)

    def analyze(self, frame):
        from roi import annotate
        canvas,scale,left,top = letterbox(frame,self.size)
        blob = cv2.dnn.blobFromImage(canvas,1/255.,(self.size,self.size),swapRB=True,crop=False)
        self.net.setInput(blob)
        detections = decode(self.net.forward(),frame.shape,scale,left,top,
                            self.confidence,self.iou,self.classes)
        return annotate(frame,detections)
