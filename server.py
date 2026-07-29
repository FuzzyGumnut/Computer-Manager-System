#!/usr/bin/env python3
"""
Computer Management Server
Central server for managing remote machines
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Set
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComputerManagerServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.client_info: Dict[str, dict] = {}
        
    async def register_client(self, websocket, client_id):
        """Register a new client"""
        self.clients[client_id] = websocket
        self.client_info[client_id] = {
            'connected_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'status': 'online'
        }
        logger.info(f"Client {client_id} connected")
        
    async def unregister_client(self, client_id):
        """Unregister a client"""
        if client_id in self.clients:
            del self.clients[client_id]
            self.client_info[client_id]['status'] = 'offline'
            self.client_info[client_id]['last_seen'] = datetime.now().isoformat()
            logger.info(f"Client {client_id} disconnected")
    
    async def broadcast_to_all(self, message):
        """Send message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients.values()],
                return_exceptions=True
            )
    
    async def send_to_client(self, client_id, message):
        """Send message to specific client"""
        if client_id in self.clients:
            await self.clients[client_id].send(json.dumps(message))
        else:
            # Silently skip - client may have disconnected
            pass
    
    async def handle_client_message(self, websocket, client_id, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'heartbeat':
                self.client_info[client_id]['last_seen'] = datetime.now().isoformat()
                await websocket.send(json.dumps({'type': 'heartbeat_ack'}))
                
            elif msg_type == 'system_info':
                self.client_info[client_id]['system_info'] = data.get('info')
                logger.info(f"Received system info from {client_id}")
                
            elif msg_type == 'screen_capture':
                # Forward screen capture to web clients
                logger.info(f"Received screen capture from {client_id}")
                await self.broadcast_to_all({
                    'type': 'screen_update',
                    'client_id': client_id,
                    'image': data.get('image')
                })
                
            elif msg_type == 'terminal_output':
                # Forward terminal output to web clients
                await self.broadcast_to_all({
                    'type': 'terminal_output',
                    'client_id': client_id,
                    'output': data.get('output')
                })
                
            elif msg_type == 'command_result':
                # Forward command result to web clients
                await self.broadcast_to_all({
                    'type': 'command_result',
                    'client_id': client_id,
                    'result': data.get('result')
                })
                
            elif msg_type == 'directory_list':
                # Forward directory listing to web clients
                await self.broadcast_to_all({
                    'type': 'directory_list',
                    'client_id': client_id,
                    'path': data.get('path'),
                    'files': data.get('files')
                })
                
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {client_id}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
    
    async def handle_web_client_message(self, websocket, message):
        """Handle message from web client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'get_clients':
                await websocket.send(json.dumps({
                    'type': 'clients_list',
                    'clients': self.client_info
                }))
                
            elif msg_type == 'send_command':
                client_id = data.get('client_id')
                command = data.get('command')
                await self.send_to_client(client_id, {
                    'type': 'execute_command',
                    'command': command
                })
                
            elif msg_type == 'start_terminal':
                client_id = data.get('client_id')
                await self.send_to_client(client_id, {
                    'type': 'start_terminal'
                })
                
            elif msg_type == 'terminal_input':
                client_id = data.get('client_id')
                input_text = data.get('input')
                await self.send_to_client(client_id, {
                    'type': 'terminal_input',
                    'input': input_text
                })
                
            elif msg_type == 'start_screen_share':
                client_id = data.get('client_id')
                await self.send_to_client(client_id, {
                    'type': 'start_screen_share'
                })
                
            elif msg_type == 'stop_screen_share':
                client_id = data.get('client_id')
                await self.send_to_client(client_id, {
                    'type': 'stop_screen_share'
                })
                
            elif msg_type == 'list_directory':
                client_id = data.get('client_id')
                path = data.get('path', '.')
                await self.send_to_client(client_id, {
                    'type': 'list_directory',
                    'path': path
                })
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON from web client")
        except Exception as e:
            logger.error(f"Error handling web client message: {e}")
    
    async def handle_agent_connection(self, websocket, path):
        """Handle connection from remote agent"""
        try:
            # Get client ID from handshake
            client_id = await websocket.recv()
            client_id = json.loads(client_id).get('client_id')
            
            if not client_id:
                client_id = str(uuid.uuid4())
                await websocket.send(json.dumps({'client_id': client_id}))
            
            await self.register_client(websocket, client_id)
            
            try:
                async for message in websocket:
                    await self.handle_client_message(websocket, client_id, message)
            finally:
                await self.unregister_client(client_id)
                
        except Exception as e:
            logger.error(f"Error in agent connection: {e}")
    
    async def handle_web_connection(self, websocket, path):
        """Handle connection from web client"""
        try:
            logger.info("Web client connected")
            async for message in websocket:
                await self.handle_web_client_message(websocket, message)
        except Exception as e:
            logger.error(f"Error in web connection: {e}")
    
    async def handle_connection(self, websocket):
        """Handle connection - determine if agent or web client"""
        try:
            # Wait for first message to determine connection type
            first_message = await websocket.recv()
            data = json.loads(first_message)
            
            if 'client_id' in data:
                # This is an agent connection
                client_id = data.get('client_id')
                if not client_id:
                    client_id = str(uuid.uuid4())
                    await websocket.send(json.dumps({'client_id': client_id}))
                
                await self.register_client(websocket, client_id)
                
                try:
                    async for message in websocket:
                        await self.handle_client_message(websocket, client_id, message)
                finally:
                    await self.unregister_client(client_id)
            else:
                # This is a web client connection
                logger.info("Web client connected")
                # Handle the first message as a regular web client message
                await self.handle_web_client_message(websocket, first_message)
                async for message in websocket:
                    await self.handle_web_client_message(websocket, message)
                    
        except Exception as e:
            logger.error(f"Error in connection: {e}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting server on {self.host}:{self.port}")
        
        # Start single server for both agents and web clients with increased message size
        async with websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            max_size=10 * 1024 * 1024  # 10MB max message size
        ):
            logger.info(f"Server is running on {self.host}:{self.port}")
            # Keep the server running
            await asyncio.Future()  # Run forever

def main():
    server = ComputerManagerServer()
    asyncio.run(server.start_server())

if __name__ == '__main__':
    main()
