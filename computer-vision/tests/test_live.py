import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from http.server import ThreadingHTTPServer
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from live import load_settings,serve_arguments
from camera import Camera
from demand_server import main as server_main

TOKEN='test-token-with-more-than-24-characters'

class LiveSettingsTests(unittest.TestCase):
    def test_file_overrides_old_export_without_executing_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env.pi'
            path.write_text('# camera settings\nTERRA_PI_TOKEN="'+TOKEN+'"\nTERRA_CAMERA=pi\n')
            with patch.dict(os.environ,{'TERRA_PI_TOKEN':'old-export'}):
                settings=load_settings(path)
            self.assertEqual(settings['TERRA_PI_TOKEN'],TOKEN)
            self.assertEqual(settings['TERRA_CAMERA'],'pi')

    def test_camera_capture_settings_do_not_require_a_token(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ,{},clear=True):
                self.assertEqual(load_settings(Path(folder)/'missing.env'),{})

    def test_live_serving_requires_roi_or_explicit_diagnostic_mode(self):
        with self.assertRaisesRegex(ValueError,'Missing roi.live.json'):
            serve_arguments({'TERRA_PI_TOKEN':TOKEN,'TERRA_ROI_FILE':'/missing/roi.json'})
        arguments=serve_arguments({'TERRA_PI_TOKEN':TOKEN},full_frame=True)
        self.assertIn('--camera',arguments)
        self.assertIn('1280',arguments)
        self.assertNotIn('--input',arguments)
        self.assertNotIn('--roi-config',arguments)

    def test_invalid_token_and_unknown_configuration_fail_clearly(self):
        for value in ('',TOKEN+'\n','YOUR_SHARED_TOKEN_FROM_LAPTOP'):
            with self.assertRaises(ValueError): serve_arguments({'TERRA_PI_TOKEN':value},True)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env.pi';path.write_text('BAD_SETTING=value\n')
            with self.assertRaises(ValueError):load_settings(path)

class CameraTests(unittest.TestCase):
    def test_pi_resolution_queue_and_cleanup(self):
        class Pi:
            def __init__(self): self.calls=0; self.closed=False
            def create_video_configuration(self,**kwargs): self.config=kwargs; return kwargs
            def configure(self,c): pass
            def start(self): pass
            def capture_array(self,name): self.calls+=1; return np.full((4,4,3),self.calls,np.uint8)
            def close(self):self.closed=True
        device=Pi()
        with patch.dict(sys.modules,{'picamera2':SimpleNamespace(Picamera2=lambda:device)}),patch('camera.time.sleep'):
            with Camera('pi',1280,720) as camera:
                self.assertEqual(camera.read()[0,0,0],1)
                self.assertEqual(camera.read()[0,0,0],2)
        self.assertEqual(device.config['main']['size'],(1280,720))
        self.assertFalse(device.config['queue'])
        self.assertTrue(device.closed)

    def test_invalid_resolution_fails_before_opening_hardware(self):
        for width,height in ((0,720),(1280,-1),(99999,720),(True,720)):
            with self.assertRaises(ValueError):Camera('pi',width,height)

class LiveHTTPTests(unittest.TestCase):
    def test_one_camera_fresh_frame_per_request_and_release_on_shutdown(self):
        class FakeCamera:
            def __init__(self):self.reads=0;self.closed=False
            def read(self):self.reads+=1;return np.full((4,4,3),self.reads,np.uint8)
            def close(self):self.closed=True
        class Pipeline:
            def __init__(self):self.calls=0
            def analyze(self,frame):self.calls+=1;return [{}]*int(frame[0,0,0]),frame
        device=FakeCamera();pipeline=Pipeline();ready=threading.Event();servers=[];errors=[]
        def factory(address,handler):
            server=ThreadingHTTPServer(('127.0.0.1',0),handler)
            servers.append(server);ready.set();return server
        def run():
            try:server_main(['--camera','pi','--width','1280','--height','720'])
            except Exception as e:errors.append(e);ready.set()
        with patch.dict(os.environ,{'TERRA_PI_TOKEN':TOKEN}),patch('camera.Camera',return_value=device) as constructor,\
             patch('vehicle_pipeline.create_pipeline',return_value=pipeline),patch('main.save_image'),\
             patch('demand_server.ThreadingHTTPServer',side_effect=factory):
            thread=threading.Thread(target=run);thread.start()
            try:
                self.assertTrue(ready.wait(5));self.assertFalse(errors)
                self.assertEqual(pipeline.calls,0)
                for expected in (2,3):
                    req=Request(f'http://127.0.0.1:{servers[0].server_port}/detect',data=b'',method='POST',headers={'Authorization':'Bearer '+TOKEN})
                    with urlopen(req,timeout=5) as response:result=json.load(response)
                    self.assertEqual(set(result),{'timeStamp','numOfCarsParked'})
                    self.assertEqual(result['numOfCarsParked'],expected)
            finally:
                if servers:servers[0].shutdown()
                thread.join(5)
            constructor.assert_called_once_with('pi',1280,720)
        self.assertTrue(device.closed)
        self.assertEqual(pipeline.calls,2)
        self.assertFalse(errors)

    def test_camera_released_if_port_cannot_be_bound(self):
        device=SimpleNamespace(read=lambda:np.zeros((4,4,3),np.uint8),close=lambda:None)
        with patch.dict(os.environ,{'TERRA_PI_TOKEN':TOKEN}),patch('camera.Camera',return_value=device),\
             patch('vehicle_pipeline.create_pipeline'),patch('main.save_image'),\
             patch.object(device,'close') as close,patch('demand_server.ThreadingHTTPServer',side_effect=OSError('port busy')):
            with self.assertRaises(OSError):server_main(['--camera','pi'])
        close.assert_called_once()

if __name__=='__main__':unittest.main()
