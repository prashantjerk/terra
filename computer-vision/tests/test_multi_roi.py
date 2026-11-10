import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from roi import LotROI,annotate

class MultiROITests(unittest.TestCase):
    def load(self,config):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'roi.json';path.write_text(json.dumps(config));return LotROI.load(path)

    def test_separate_areas_exclude_aisle_and_overlaps_count_once(self):
        left=[[0,0],[.3,0],[.3,1],[0,1]]
        right=[[.7,0],[1,0],[1,1],[.7,1]]
        roi=self.load({'polygons':[left,right,left]})
        frame=np.zeros((101,101,3),np.uint8)
        ds=[{'number':i,'class':'car','confidence':.9,'box_xywh':[x,20,10,10]}
            for i,x in enumerate([5,45,85],1)]
        counted,_=annotate(frame,ds,roi)
        self.assertEqual(len(counted),2)
        self.assertEqual([d['number'] for d in counted],[1,2])

    def test_reference_rejects_aspect_change_but_allows_scaled_same_view(self):
        roi=self.load({'reference_size':[1920,1080],'polygon':[[0,0],[1,0],[1,1],[0,1]]})
        self.assertEqual(len(roi.polygons((720,1280,3))),1)
        with self.assertRaisesRegex(ValueError,'aspect ratio'):roi.polygons((480,640,3))

    def test_malformed_multi_configs_fail(self):
        for config in ({'polygons':[]},{'polygons':[None]}, {'polygon':[], 'polygons':[]},
                       {'polygon':[[0,0],[1,0],[1,1]],'reference_size':[0,1080]}):
            with self.assertRaises(ValueError):self.load(config)

    def test_stationed_view_anchors_keep_parking_and_exclude_background(self):
        roi=LotROI.load(Path(__file__).resolve().parents[1]/'roi.position-20261110.json')
        def inside(x,y):return roi.contains({'box_xywh':[x-1,y-2,2,2]},(1080,1920,3))
        for point in [(590,590),(560,800),(730,267),(755,112),(225,278),(337,150),(79,462)]:
            self.assertTrue(inside(*point),point)
        for point in [(390,400),(1200,500),(710,150),(500,1010),(500,950),(485,43)]:
            self.assertFalse(inside(*point),point)

class TwelveSpaceTests(unittest.TestCase):
    def test_user_confirmed_preset_has_twelve_valid_spaces(self):
        roi=LotROI.load(Path(__file__).resolve().parents[1]/'roi.spaces-12-20261110.json')
        self.assertEqual(len(roi.areas),12)
        self.assertEqual(roi.capacity,12)
        self.assertEqual(roi.anchor_mode,'center')
        for x,y in [(480,870),(545,660),(575,470),(620,355),(685,269),(710,190),
                    (747,73),(797,23),(90,350),(225,215),(355,90),(500,25)]:
            self.assertTrue(roi.contains({'box_xywh':[x-10,y-10,20,20]},(1080,1920,3)),(x,y))
        for x,y in [(390,400),(1200,500),(500,1070),(450,180)]:
            self.assertFalse(roi.contains({'box_xywh':[x-10,y-10,20,20]},(1080,1920,3)),(x,y))

    def test_center_anchor_keeps_a_vehicle_whose_bottom_is_outside_body_outline(self):
        points=[[.2,.2],[.8,.2],[.8,.6],[.2,.6]]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'roi.json';path.write_text(json.dumps({'polygon':points,'anchor':'center'}))
            centered=LotROI.load(path)
        detection={'box_xywh':[40,30,20,50]}
        self.assertTrue(centered.contains(detection,(101,101,3)))
        self.assertFalse(LotROI(points).contains(detection,(101,101,3)))

    def test_unknown_anchor_or_invalid_capacity_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'roi.json'
            for option in ({'anchor':'unknown'},{'capacity':0},{'capacity':True}):
                path.write_text(json.dumps({'polygon':[[0,0],[1,0],[1,1]],**option}))
                with self.assertRaises(ValueError):LotROI.load(path)

if __name__=='__main__':unittest.main()
