#!/usr/bin/env python3
"""
Computer Manager Server GUI (Built-in WebSocket Server)
"""

import sys
import json
import asyncio
import base64
import io
import numpy as np
import sounddevice as sd
import socket
import urllib.request
import urllib.error
from PIL import Image

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QLabel, QTextEdit, QLineEdit, QPushButton, 
                             QTabWidget, QTreeWidget, QTreeWidgetItem, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QImage, QPixmap, QTextCursor

import websockets


class InteractiveScreenLabel(QLabel):
    def __init__(self, parent=None, server_gui=None):
        super().__init__(parent)
        self.server_gui = server_gui
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event):
        self.setFocus()
        if not self.pixmap() or not self.server_gui or not self.server_gui.selected_client:
            return

        # Calculate coordinates relative to rendered pixmap frame
        pixmap_size = self.pixmap().size()
        lbl_size = self.size()
        
        # Calculate image offset caused by AspectRatio alignment
        offset_x = (lbl_size.width() - pixmap_size.width()) / 2
        offset_y = (lbl_size.height() - pixmap_size.height()) / 2
        
        click_x = event.position().x() - offset_x
        click_y = event.position().y() - offset_y

        if 0 <= click_x <= pixmap_size.width() and 0 <= click_y <= pixmap_size.height():
            x_pct = click_x / pixmap_size.width()
            y_pct = click_y / pixmap_size.height()
            
            button_map = {
                Qt.MouseButton.LeftButton: 'left',
                Qt.MouseButton.RightButton: 'right',
                Qt.MouseButton.MiddleButton: 'middle'
            }
            button = button_map.get(event.button(), 'left')

            self.server_gui.send_input({
                'event': 'mouse_click',
                'x_pct': x_pct,
                'y_pct': y_pct,
                'button': button
            })

    def keyPressEvent(self, event):
        if not self.server_gui or not self.server_gui.selected_client:
            return

        key_map = {
            Qt.Key.Key_Return: 'enter',
            Qt.Key.Key_Backspace: 'backspace',
            Qt.Key.Key_Tab: 'tab',
            Qt.Key.Key_Escape: 'escape',
            Qt.Key.Key_Delete: 'delete',
            Qt.Key.Key_Up: 'up',
            Qt.Key.Key_Down: 'down',
            Qt.Key.Key_Left: 'left',
            Qt.Key.Key_Right: 'right',
            Qt.Key.Key_Space: 'space'
        }

        key = key_map.get(event.key())
        if key:
            self.server_gui.send_input({'event': 'key_press', 'key': key})
        else:
            text = event.text()
            if text:
                self.server_gui.send_input({'event': 'type_text', 'text': text})


class WebSocketServerThread(QThread):
    """Runs a websockets server in a background thread."""
    message_received = pyqtSignal(str, dict)  # (client_id, data)
    client_connected = pyqtSignal(str, dict)   # (client_id, info)
    client_disconnected = pyqtSignal(str)     # (client_id)

    def __init__(self, host='0.0.0.0', port=8765):
        super().__init__()
        self.host = host
        self.port = port
        self.clients = {}  # client_id -> websocket
        self.event_loop = None
        self.running = True

    def run(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self.start_server())

    async def start_server(self):
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"WebSocket Server listening on ws://{self.host}:{self.port}")
            while self.running:
                await asyncio.sleep(1)

    async def handle_client(self, websocket):
        client_id = None
        try:
            # First message from client contains client_id and system_info
            first_msg = await websocket.recv()
            data = json.loads(first_msg)
            client_id = data.get('client_id')

            if client_id:
                self.clients[client_id] = websocket
                info = data.get('info', {})
                self.client_connected.emit(client_id, info)

                # Listen for messages from this client
                async for message in websocket:
                    msg_data = json.loads(message)
                    self.message_received.emit(client_id, msg_data)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            if client_id and client_id in self.clients:
                del self.clients[client_id]
                self.client_disconnected.emit(client_id)

    def send_to_client(self, client_id, message):
        if client_id in self.clients and self.event_loop:
            ws = self.clients[client_id]
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps(message)),
                self.event_loop
            )


class ServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Computer Manager Server")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QWidget { background-color: #1a1a2e; color: #ffffff; }
            QListWidget { background-color: #0f0f23; border: none; padding: 5px; }
            QListWidget::item { padding: 8px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #60a5fa; color: #ffffff; }
            QTextEdit { background-color: #0f0f23; border: none; padding: 10px; }
            QLineEdit { background-color: #0f0f23; border: 1px solid #60a5fa; padding: 8px; border-radius: 4px; }
            QPushButton { background-color: #60a5fa; color: #ffffff; border: none; padding: 8px 16px; border-radius: 4px; }
            QPushButton:hover { background-color: #3b82f6; }
            QTabWidget::pane { border: none; background-color: #1a1a2e; }
            QTabBar::tab { background-color: #16213e; color: #ffffff; padding: 8px 16px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: #60a5fa; }
            QTreeWidget { background-color: #0f0f23; border: none; }
            QTreeWidget::item { padding: 5px; }
            QTreeWidget::item:selected { background-color: #60a5fa; color: #ffffff; }
            QHeaderView::section { background-color: #16213e; color: #60a5fa; padding: 8px; border: none; }
        """)

        self.client_data = {}  # client_id -> info
        self.selected_client = None
        self.current_path = '.'
        
        # Initialize audio output stream
        self.audio_stream = sd.OutputStream(samplerate=16000, channels=1, dtype='int16')
        self.audio_stream.start()

        self.setup_ui()
        self.setup_server()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel - Client list
        left_panel = QWidget()
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet("background-color: #16213e; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)

        title_label = QLabel("Connected Clients")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #60a5fa; padding: 10px;")
        left_layout.addWidget(title_label)

        self.client_list = QListWidget()
        self.client_list.itemClicked.connect(self.on_client_select)
        left_layout.addWidget(self.client_list)

        self.status_label = QLabel("Server Running on :8765")
        self.status_label.setStyleSheet("color: #22c55e; padding: 10px;")
        left_layout.addWidget(self.status_label)

        # GitHub token input
        github_label = QLabel("GitHub Token:")
        github_label.setStyleSheet("color: #60a5fa; padding: 5px;")
        left_layout.addWidget(github_label)

        self.github_token_input = QLineEdit()
        self.github_token_input.setPlaceholderText("ghp_xxxxxxxxxxxx")
        self.github_token_input.setStyleSheet("background-color: #0f0f23; border: 1px solid #60a5fa; padding: 5px; border-radius: 4px;")
        left_layout.addWidget(self.github_token_input)

        self.update_github_btn = QPushButton("Update GitHub IP")
        self.update_github_btn.clicked.connect(self.update_github_ip)
        self.update_github_btn.setStyleSheet("background-color: #22c55e; color: #ffffff; border: none; padding: 8px; border-radius: 4px;")
        left_layout.addWidget(self.update_github_btn)

        main_layout.addWidget(left_panel)

        # Right panel - Main content
        self.tab_widget = QTabWidget()

        # Screen tab
        self.screen_widget = QWidget()
        screen_layout = QVBoxLayout(self.screen_widget)

        # Controls header
        screen_controls = QHBoxLayout()
        self.start_screen_btn = QPushButton("Start Screen Share")
        self.start_screen_btn.clicked.connect(self.start_screen_share)
        screen_controls.addWidget(self.start_screen_btn)

        self.stop_screen_btn = QPushButton("Stop Screen Share")
        self.stop_screen_btn.clicked.connect(self.stop_screen_share)
        screen_controls.addWidget(self.stop_screen_btn)

        screen_controls.addStretch()
        
        self.black_screen_btn = QPushButton("Enable Black Screen")
        self.black_screen_btn.setCheckable(True)
        self.black_screen_btn.clicked.connect(self.toggle_black_screen)
        screen_controls.addWidget(self.black_screen_btn)
        
        self.start_audio_btn = QPushButton("Start Audio")
        self.start_audio_btn.clicked.connect(self.start_audio)
        screen_controls.addWidget(self.start_audio_btn)
        
        self.stop_audio_btn = QPushButton("Stop Audio")
        self.stop_audio_btn.clicked.connect(self.stop_audio)
        screen_controls.addWidget(self.stop_audio_btn)
        
        screen_layout.addLayout(screen_controls)

        # Container for smooth, non-zooming layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background: #000;")

        self.screen_label = InteractiveScreenLabel("No screen selected", server_gui=self)
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setStyleSheet("color: #6b7280; font-size: 16px;")
        
        self.scroll_area.setWidget(self.screen_label)
        screen_layout.addWidget(self.scroll_area, 1)

        self.tab_widget.addTab(self.screen_widget, "Screen")

        # Terminal tab
        self.terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(self.terminal_widget)

        terminal_controls = QHBoxLayout()
        self.start_terminal_btn = QPushButton("Start Terminal")
        self.start_terminal_btn.clicked.connect(self.start_terminal)
        terminal_controls.addWidget(self.start_terminal_btn)

        terminal_controls.addStretch()
        terminal_layout.addLayout(terminal_controls)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("font-family: 'Monaco', 'Courier New', monospace; font-size: 12px;")
        terminal_layout.addWidget(self.terminal_output)

        terminal_input_layout = QHBoxLayout()
        prompt_label = QLabel("$")
        prompt_label.setStyleSheet("color: #22c55e; font-weight: bold; font-family: 'Monaco', monospace;")
        terminal_input_layout.addWidget(prompt_label)

        self.terminal_input = QLineEdit()
        self.terminal_input.returnPressed.connect(self.send_terminal_command)
        self.terminal_input.setStyleSheet("font-family: 'Monaco', 'Courier New', monospace; font-size: 12px;")
        terminal_input_layout.addWidget(self.terminal_input)

        terminal_layout.addLayout(terminal_input_layout)
        self.tab_widget.addTab(self.terminal_widget, "Terminal")

        # Webcam tab
        self.webcam_widget = QWidget()
        webcam_layout = QVBoxLayout(self.webcam_widget)

        webcam_controls = QHBoxLayout()
        self.start_webcam_btn = QPushButton("Start Webcam")
        self.start_webcam_btn.clicked.connect(self.start_webcam_share)
        webcam_controls.addWidget(self.start_webcam_btn)

        self.stop_webcam_btn = QPushButton("Stop Webcam")
        self.stop_webcam_btn.clicked.connect(self.stop_webcam_share)
        webcam_controls.addWidget(self.stop_webcam_btn)

        webcam_controls.addStretch()
        webcam_layout.addLayout(webcam_controls)

        self.webcam_label = QLabel("Webcam disabled")
        self.webcam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.webcam_label.setStyleSheet("color: #6b7280; font-size: 16px;")
        webcam_layout.addWidget(self.webcam_label, 1)

        self.tab_widget.addTab(self.webcam_widget, "Webcam")

        # Presets tab
        self.preset_widget = QWidget()
        preset_layout = QVBoxLayout(self.preset_widget)

        grid = QGridLayout()
        
        btn_ip = QPushButton("Check IP Config")
        btn_ip.clicked.connect(lambda: self.trigger_preset('check_ip'))
        grid.addWidget(btn_ip, 0, 0)

        btn_dns = QPushButton("Flush DNS")
        btn_dns.clicked.connect(lambda: self.trigger_preset('flush_dns'))
        grid.addWidget(btn_dns, 0, 1)

        btn_ports = QPushButton("List Open Ports")
        btn_ports.clicked.connect(lambda: self.trigger_preset('list_ports'))
        grid.addWidget(btn_ports, 1, 0)

        btn_sys = QPushButton("System Info")
        btn_sys.clicked.connect(lambda: self.trigger_preset('system_info'))
        grid.addWidget(btn_sys, 1, 1)

        preset_layout.addLayout(grid)

        self.preset_output = QTextEdit()
        self.preset_output.setReadOnly(True)
        preset_layout.addWidget(self.preset_output)

        self.tab_widget.addTab(self.preset_widget, "Presets")

        # Files tab
        self.files_widget = QWidget()
        files_layout = QVBoxLayout(self.files_widget)

        nav_layout = QHBoxLayout()
        home_btn = QPushButton("Home")
        home_btn.clicked.connect(self.go_to_home)
        nav_layout.addWidget(home_btn)

        up_btn = QPushButton("Up")
        up_btn.clicked.connect(self.go_up)
        nav_layout.addWidget(up_btn)

        self.path_label = QLabel(".")
        self.path_label.setStyleSheet("color: #60a5fa; padding: 0 10px;")
        nav_layout.addWidget(self.path_label)

        nav_layout.addStretch()
        files_layout.addLayout(nav_layout)

        self.file_tree = QTreeWidget()
        self.file_tree.setColumnCount(3)
        self.file_tree.setHeaderLabels(["Name", "Size", "Type"])
        self.file_tree.itemDoubleClicked.connect(self.on_file_double_click)
        files_layout.addWidget(self.file_tree)

        self.tab_widget.addTab(self.files_widget, "Files")
        main_layout.addWidget(self.tab_widget)

    def setup_server(self):
        self.server_thread = WebSocketServerThread(host='10.121.112.164', port=8765)
        self.server_thread.message_received.connect(self.handle_client_message)
        self.server_thread.client_connected.connect(self.on_client_connected)
        self.server_thread.client_disconnected.connect(self.on_client_disconnected)
        self.server_thread.start()

    def on_client_connected(self, client_id, info):
        hostname = info.get('hostname', 'Unknown')
        self.client_data[client_id] = info
        self.client_list.addItem(f"{hostname} ({client_id[:8]}...)")

    def on_client_disconnected(self, client_id):
        if client_id in self.client_data:
            del self.client_data[client_id]
        self.refresh_client_list_ui()
        if self.selected_client == client_id:
            self.selected_client = None

    def refresh_client_list_ui(self):
        self.client_list.clear()
        for cid, info in self.client_data.items():
            hostname = info.get('hostname', 'Unknown')
            self.client_list.addItem(f"{hostname} ({cid[:8]}...)")

    def on_client_select(self, item):
        index = self.client_list.row(item)
        cids = list(self.client_data.keys())
        if index < len(cids):
            self.selected_client = cids[index]
            self.request_directory('.')
            self.start_terminal()

    def handle_client_message(self, client_id, data):
        if client_id != self.selected_client:
            return

        msg_type = data.get('type')
        if msg_type == 'screen_capture':
            self.update_screen(data.get('image'))
        elif msg_type == 'webcam_capture':
            self.update_webcam(data.get('image'))
        elif msg_type == 'terminal_output':
            self.terminal_output.append(data.get('output', ''))
            self.terminal_output.moveCursor(QTextCursor.MoveOperation.End)
        elif msg_type == 'directory_list':
            self.update_file_list(data.get('files', []), data.get('path', '.'))
        elif msg_type == 'audio_chunk':
            self.play_audio_chunk(data.get('data'))
        elif msg_type == 'preset_output':
            self.display_preset_output(data)

    def update_screen(self, image_data):
        try:
            image_bytes = base64.b64decode(image_data)
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes, "JPEG")

            if not pixmap.isNull():
                # Scale relative to the viewport size, NEVER the label size
                viewport_size = self.scroll_area.viewport().size()
                
                # SmoothTransformation produces sharp crisp visuals
                scaled_pixmap = pixmap.scaled(
                    viewport_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.screen_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error updating screen: {e}")

    def update_webcam(self, image_data):
        try:
            image_bytes = base64.b64decode(image_data)
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes, "JPEG")

            if not pixmap.isNull():
                target_size = self.webcam_widget.size()
                scaled_pixmap = pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation
                )
                self.webcam_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error updating webcam: {e}")

    def send_terminal_command(self):
        if self.selected_client:
            command = self.terminal_input.text()
            if command:
                self.server_thread.send_to_client(self.selected_client, {
                    'type': 'terminal_input',
                    'input': command + '\n'
                })
                self.terminal_input.clear()

    def start_terminal(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'start_terminal'})

    def start_screen_share(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'start_screen_share'})

    def stop_screen_share(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'stop_screen_share'})

    def start_webcam_share(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'start_webcam_share'})

    def stop_webcam_share(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'stop_webcam_share'})

    def request_directory(self, path='.'):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {
                'type': 'list_directory',
                'path': path
            })

    def update_file_list(self, files, path):
        self.current_path = path
        self.path_label.setText(path)
        self.file_tree.clear()

        for file in files:
            file_type = 'Directory' if file.get('is_dir') else 'File'
            size = file.get('size', 0)
            size_str = f"{size} B" if size < 1024 else f"{size/1024:.1f} KB"
            item = QTreeWidgetItem([file.get('name'), size_str, file_type])
            item.setData(0, Qt.ItemDataRole.UserRole, file.get('path'))
            self.file_tree.addTopLevelItem(item)

    def on_file_double_click(self, item, column):
        file_type = item.text(2)
        full_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_type == 'Directory' and full_path:
            self.request_directory(full_path)

    def toggle_black_screen(self):
        if not self.selected_client:
            return
            
        if self.black_screen_btn.isChecked():
            self.black_screen_btn.setText("Disable Black Screen")
            self.black_screen_btn.setStyleSheet("background-color: #991b1b; color: white;")
            self.server_thread.send_to_client(self.selected_client, {'type': 'enable_black_screen'})
        else:
            self.black_screen_btn.setText("Enable Black Screen")
            self.black_screen_btn.setStyleSheet("")
            self.server_thread.send_to_client(self.selected_client, {'type': 'disable_black_screen'})

    def send_input(self, input_data):
        if self.selected_client:
            self.server_thread.send_to_client(
                self.selected_client,
                {'type': 'input_event', **input_data}
            )

    def play_audio_chunk(self, raw_b64):
        try:
            pcm_bytes = base64.b64decode(raw_b64)
            audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)
            self.audio_stream.write(audio_data)
        except Exception as e:
            print(f"Audio playback error: {e}")

    def start_audio(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'start_audio'})

    def stop_audio(self):
        if self.selected_client:
            self.server_thread.send_to_client(self.selected_client, {'type': 'stop_audio'})

    def trigger_preset(self, preset_key):
        if self.selected_client:
            self.preset_output.append(f"--- Running {preset_key} ---")
            self.server_thread.send_to_client(
                self.selected_client, 
                {'type': 'run_preset', 'preset': preset_key}
            )

    def display_preset_output(self, data):
        self.preset_output.append(data.get('output', 'No output received.'))

    def go_to_home(self):
        self.request_directory('.')

    def go_up(self):
        parent_path = "/".join(self.current_path.rstrip("/").split("/")[:-1])
        self.request_directory(parent_path if parent_path else '/')

    def get_local_ip(self):
        """Get the local IP address of the machine"""
        try:
            # Create a socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"Error getting local IP: {e}")
            return None

    def update_github_ip(self):
        """Update the clientip.txt file on GitHub with local IP"""
        token = self.github_token_input.text().strip()
        if not token:
            self.status_label.setText("Error: GitHub token required")
            self.status_label.setStyleSheet("color: #ef4444; padding: 10px;")
            return

        local_ip = self.get_local_ip()
        if not local_ip:
            self.status_label.setText("Error: Could not get local IP")
            self.status_label.setStyleSheet("color: #ef4444; padding: 10px;")
            return

        try:
            # GitHub API to update file
            url = "https://api.github.com/repos/FuzzyGumnut/Computer-Manager-System/contents/clientip.txt"
            
            # First, get the current file to get its SHA
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"token {token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "Computer-Manager-System")
            
            sha = None
            try:
                response = urllib.request.urlopen(req)
                data = json.loads(response.read().decode('utf-8'))
                sha = data.get('sha')
                print(f"File exists, SHA: {sha}")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print("File does not exist yet, will create new")
                    sha = None
                else:
                    print(f"HTTP Error checking file: {e.code} - {e.reason}")
                    raise

            # Prepare the update
            content = base64.b64encode(local_ip.encode('utf-8')).decode('utf-8')
            message = f"Update server IP to {local_ip}"
            
            update_data = {
                "message": message,
                "content": content
            }
            
            if sha:
                update_data["sha"] = sha

            # Send the update
            req = urllib.request.Request(url, data=json.dumps(update_data).encode('utf-8'), method='PUT')
            req.add_header("Authorization", f"token {token}")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "Computer-Manager-System")
            
            print(f"Sending update request to GitHub...")
            response = urllib.request.urlopen(req)
            print(f"Response status: {response.status}")
            
            self.status_label.setText(f"Updated GitHub IP to: {local_ip}")
            self.status_label.setStyleSheet("color: #22c55e; padding: 10px;")
            
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP Error {e.code}: {e.reason}"
            print(f"GitHub API Error: {error_msg}")
            # Try to read error response
            try:
                error_body = e.read().decode('utf-8')
                print(f"Error details: {error_body}")
            except:
                pass
            self.status_label.setText(f"Error: {error_msg}")
            self.status_label.setStyleSheet("color: #ef4444; padding: 10px;")
        except Exception as e:
            error_msg = str(e)
            print(f"Unexpected error: {error_msg}")
            self.status_label.setText(f"Error: {error_msg}")
            self.status_label.setStyleSheet("color: #ef4444; padding: 10px;")


def main():
    app = QApplication(sys.argv)
    window = ServerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()