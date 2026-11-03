import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from roi import LotROI, annotate
from yolo import decode, letterbox, YoloDetector
from vehicle_pipeline import VehiclePipeline, add_detection_arguments, create_pipeline


def prediction(cx=320,cy=320,w=100,h=100,category=2,score=.9):
    row=np.zeros(84,dtype=np.float32)
    row[:4]=[cx,cy,w,h]
    row[4+category]=score
    return row


def output(*rows):
    return np.stack(rows).T[None,:,:]


class YoloTests(unittest.TestCase):
    def test_letterbox_preserves_aspect_and_roundtrip_boxes(self):
        frame=np.zeros((320,640,3),dtype=np.uint8)
        canvas,scale,left,top=letterbox(frame,640)
        self.assertEqual(canvas.shape,(640,640,3))
        self.assertEqual((scale,left,top),(1,0,160))
        result=decode(output(prediction(300,260,100,80)),frame.shape,scale,left,top,.5,.45,[2,5,7])
        self.assertEqual(result[0]['box_xywh'],[250,60,100,80])

    def test_scale_and_padding_reverse_for_portrait_image(self):
        frame=np.zeros((1000,500,3),dtype=np.uint8)
        _,scale,left,top=letterbox(frame,640)
        self.assertEqual((scale,left,top),(.64,160,0))
        result=decode(output(prediction(320,320,64,128)),frame.shape,scale,left,top,.5,.45,[2])
        self.assertEqual(result[0]['box_xywh'],[200,400,100,200])

    def test_filters_nonvehicles_weak_scores_and_duplicates_across_classes(self):
        result=decode(output(prediction(),prediction(category=7,score=.8),
            prediction(cx=80,score=.1),prediction(cx=500,category=0)),(640,640,3),1,0,0,.5,.45,[2,5,7])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['class'],'car')

    def test_transposed_output_and_multiple_vehicles(self):
        values=output(prediction(cx=100),prediction(cx=500,category=5))
        for form in (values,values.transpose(0,2,1)):
            result=decode(form,(640,640,3),1,0,0,.5,.45,[2,5,7])
            self.assertEqual(len(result),2)
            self.assertEqual({d['class'] for d in result},{'car','bus'})

    def test_empty_bad_values_and_padding_only_boxes_are_not_counted(self):
        invalid=prediction(); invalid[0]=np.nan
        result=decode(output(prediction(cy=30,h=20),prediction(w=-1),invalid),
                      (320,640,3),1,0,160,.5,.45,[2])
        self.assertEqual(result,[])
        self.assertEqual(decode(np.zeros((1,84,0)),(640,640,3),1,0,0,.5,.45,[2]),[])

    def test_rejects_incompatible_exports(self):
        for shape in ((1,85,100),(1,100,6),(84,100)):
            with self.assertRaises(ValueError):
                decode(np.zeros(shape),(640,640,3),1,0,0,.5,.45,[2])

    def test_network_receives_rgb_normalized_blob_and_decoded_results(self):
        class Net:
            def setPreferableBackend(self,*_): pass
            def setPreferableTarget(self,*_): pass
            def setInput(self,blob): self.blob=blob
            def forward(self): return output(prediction())
        net=Net()
        with tempfile.TemporaryDirectory() as folder:
            model=Path(folder)/'test.onnx'; model.touch()
            with patch('cv2.dnn.readNetFromONNX',return_value=net):
                detector=YoloDetector(model)
        frame=np.zeros((640,640,3),np.uint8); frame[:]=[0,0,255]
        detections,annotated=detector.analyze(frame)
        self.assertEqual(len(detections),1)
        self.assertEqual(net.blob.shape,(1,3,640,640))
        self.assertEqual(float(net.blob[0,0,0,0]),1.)
        self.assertEqual(float(net.blob[0,2,0,0]),0.)
        self.assertEqual(annotated.shape,frame.shape)

    @unittest.skipUnless((Path(__file__).resolve().parents[1]/'models/yolov8n.onnx').exists(),
                         'Export the optional YOLOv8 ONNX model for the real inference test')
    def test_real_yolo_blank_image_has_no_vehicles(self):
        model=Path(__file__).resolve().parents[1]/'models/yolov8n.onnx'
        detector=YoloDetector(model)
        detections,_=detector.analyze(np.zeros((480,640,3),dtype=np.uint8))
        self.assertEqual(detections,[])

    def test_constructor_rejects_invalid_configuration(self):
        for options in ({'confidence':float('nan')},{'size':600},{'classes':[0]}):
            with self.assertRaises(ValueError): YoloDetector('missing.onnx',**options)
        with self.assertRaises(ValueError): YoloDetector(None)


class ROITests(unittest.TestCase):
    def setUp(self):
        self.frame=np.zeros((101,101,3),dtype=np.uint8)
        self.roi=LotROI([[.25,.25],[.75,.25],[.75,.75],[.25,.75]])

    def test_counts_bottom_center_including_boundary_not_box_center(self):
        self.assertTrue(self.roi.contains({'box_xywh':[40,20,20,20]},self.frame.shape))
        self.assertTrue(self.roi.contains({'box_xywh':[40,55,20,20]},self.frame.shape))
        self.assertFalse(self.roi.contains({'box_xywh':[40,60,20,30]},self.frame.shape))
        self.assertFalse(self.roi.contains({'box_xywh':[0,30,20,20]},self.frame.shape))

    def test_annotation_excludes_and_renumbers_with_full_frame_default(self):
        ds=[{'number':1,'class':'car','confidence':.9,'box_xywh':[0,30,20,20]},
            {'number':2,'class':'truck','confidence':.8,'box_xywh':[40,30,20,20]}]
        counted,image=annotate(self.frame,ds,self.roi)
        self.assertEqual(len(counted),1)
        self.assertEqual(counted[0]['number'],1)
        self.assertEqual(ds[1]['number'],2)
        self.assertFalse(np.array_equal(image,self.frame))
        self.assertEqual(len(annotate(self.frame,ds)[0]),2)

    def test_normalized_polygon_scales_with_resolution(self):
        self.assertTrue(self.roi.contains({'box_xywh':[80,60,40,40]},(201,201,3)))
        self.assertEqual(self.roi.polygon((201,201,3)).tolist()[0],[50,50])

    def test_simple_concave_polygon_supported(self):
        roi=LotROI([[0,0],[1,0],[1,1],[.5,.5],[0,1]])
        self.assertTrue(roi.contains({'box_xywh':[40,0,20,10]},self.frame.shape))
        self.assertFalse(roi.contains({'box_xywh':[40,60,20,30]},self.frame.shape))

    def test_rejects_invalid_geometry_and_malformed_json(self):
        for points in ([],[[0,0],[1,1]],[[0,0],[1,1],[0,1],[1,0]],
            [[0,0],[.5,.5],[1,1]],[[0,0],[1,0],[1,1],[0,0]],
            [[0,0],[2,0],[1,1]],[[0,0],[1,0],[True,1]],
            [[0,0],[1,0],[float('nan'),1]]):
            with self.assertRaises(ValueError): LotROI(points)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'roi.json'
            for config in ({'regions':[]}, {'polygon':[]}, []):
                path.write_text(json.dumps(config))
                with self.assertRaises(ValueError): LotROI.load(path)

    def test_shared_pipeline_filters_results(self):
        class FakeDetector:
            def analyze(self,frame):
                return [{'number':1,'class':'car','confidence':.9,'box_xywh':[0,30,20,20]},
                        {'number':2,'class':'car','confidence':.8,'box_xywh':[40,30,20,20]}],frame
        result,_=VehiclePipeline(FakeDetector(),self.roi).analyze(self.frame)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['number'],1)

    def test_ssd_rejects_yolo_only_flags_instead_of_ignoring_them(self):
        parser=argparse.ArgumentParser(); add_detection_arguments(parser)
        for options in (['--model','model.onnx'],['--classes','2'],['--imgsz','320'],['--iou','.3']):
            with self.assertRaises(ValueError): create_pipeline(parser.parse_args(options))

    def test_both_entry_points_accept_same_detector_options(self):
        parser=argparse.ArgumentParser(); add_detection_arguments(parser)
        args=parser.parse_args(['--detector','yolo','--model','test.onnx','--imgsz','320'])
        with patch('yolo.YoloDetector') as detector:
            create_pipeline(args)
        detector.assert_called_once_with(Path('test.onnx'),.5,320,.45,[2,5,7])


if __name__=='__main__': unittest.main()
