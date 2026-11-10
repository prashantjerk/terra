"""Prepare one camera frame or start on-demand live detection using .env.pi."""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'TERRA_PI_TOKEN','TERRA_CAMERA','TERRA_WIDTH','TERRA_HEIGHT',
           'TERRA_DETECTOR','TERRA_ROI_FILE','TERRA_CONFIDENCE','TERRA_MODEL'}


def load_settings(path):
    settings = {key: os.environ[key] for key in ALLOWED if key in os.environ}
    if path.is_file():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                raise ValueError(f'{path.name} line {number}: expected NAME=value')
            key, value = line.split('=',1)
            key, value = key.strip(), value.strip()
            if key not in ALLOWED:
                raise ValueError(f'{path.name} line {number}: unsupported setting name')
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            # File takes priority so old exports cannot silently override it.
            settings[key] = value
    return settings


def relative_path(value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def serve_arguments(settings, full_frame=False):
    token = settings.get('TERRA_PI_TOKEN','')
    if len(token) < 24 or any(c.isspace() for c in token) or token.startswith('YOUR_'):
        raise ValueError('Set TERRA_PI_TOKEN in .env.pi to the exact laptop token, on one line')
    args = ['--camera', settings.get('TERRA_CAMERA','pi'),
            '--width', settings.get('TERRA_WIDTH','1280'),
            '--height', settings.get('TERRA_HEIGHT','720'),
            '--detector',settings.get('TERRA_DETECTOR','ssd'),
            '--confidence',settings.get('TERRA_CONFIDENCE','0.5')]
    if not full_frame:
        roi = relative_path(settings.get('TERRA_ROI_FILE','roi.live.json'))
        if not roi.is_file():
            raise ValueError('Missing roi.live.json. Capture a camera photo and use roi-editor.html to mark the lot; --full-frame is available for diagnostics')
        args += ['--roi-config',str(roi)]
    if settings.get('TERRA_DETECTOR','ssd') == 'yolo':
        args += ['--model',str(relative_path(settings.get('TERRA_MODEL','models/yolov8n.onnx')))]
    return args


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['capture','serve'])
    parser.add_argument('--env-file',type=Path,default=ROOT/'.env.pi')
    parser.add_argument('--full-frame',action='store_true',help='Diagnostic counting across the entire image')
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.env_file)
        if args.command == 'capture':
            from camera import Camera
            from main import save_image
            source = settings.get('TERRA_CAMERA','pi')
            source = '0' if source == 'usb' else source
            if source != 'pi' and not source.isdigit():
                raise ValueError('TERRA_CAMERA must be pi, usb, or a nonnegative camera index')
            with Camera(source,int(settings.get('TERRA_WIDTH','1280')),int(settings.get('TERRA_HEIGHT','720'))) as camera:
                save_image(ROOT/'captures/live-frame.jpg',camera.read())
            print(f'Saved {ROOT / "captures/live-frame.jpg"}',flush=True)
        else:
            from demand_server import main as serve
            arguments = serve_arguments(settings,args.full_frame)
            os.environ['TERRA_PI_TOKEN'] = settings['TERRA_PI_TOKEN']
            serve(arguments)
    except (ValueError,RuntimeError,OSError) as exc:
        parser.exit(1,f'Live camera setup failed: {exc}\n')

if __name__ == '__main__':
    main()
