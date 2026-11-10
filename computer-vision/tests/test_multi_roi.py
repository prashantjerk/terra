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

if __name__=='__main__':unittest.main()
