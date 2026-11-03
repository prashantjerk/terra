"""Shared detector/ROI wiring for saved photos and the on-demand Pi service."""
from pathlib import Path
from roi import LotROI, annotate


def add_detection_arguments(parser):
    parser.add_argument('--detector',choices=['ssd','yolo'],default='ssd')
    parser.add_argument('--model',type=Path,help='YOLOv8 COCO ONNX model path')
    parser.add_argument('--roi-config',type=Path,help='Normalized lot polygon JSON; omitted means full frame')
    parser.add_argument('--confidence',type=float,default=.5)
    parser.add_argument('--imgsz',type=int,help='YOLO default 640; must match the static ONNX export size')
    parser.add_argument('--iou',type=float,help='YOLO duplicate-box suppression threshold (default 0.45)')
    parser.add_argument('--classes',type=int,nargs='+',help='YOLO COCO vehicle IDs: 2 car, 3 motorcycle, 5 bus, 7 truck')


class VehiclePipeline:
    def __init__(self, detector, roi=None):
        self.detector,self.roi = detector,roi

    def analyze(self, frame):
        detections,_ = self.detector.analyze(frame)
        # Redraw from the original frame so excluded boxes never retain counted labels.
        return annotate(frame,detections,self.roi)


def create_pipeline(args):
    # Validate ROI before spending time loading a model. Configuration is fixed at startup.
    roi = LotROI.load(args.roi_config) if args.roi_config else None
    if args.detector == 'yolo':
        from yolo import YoloDetector
        detector = YoloDetector(args.model,args.confidence,
                                args.imgsz if args.imgsz is not None else 640,
                                args.iou if args.iou is not None else .45,
                                args.classes if args.classes is not None else [2,5,7])
    else:
        if any(value is not None for value in (args.model,args.imgsz,args.iou,args.classes)):
            raise ValueError('--model, --imgsz, --iou and --classes require --detector yolo')
        from vehicles import VehicleDetector
        detector = VehicleDetector(args.confidence)
    return VehiclePipeline(detector,roi)
