#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 10:15:23 2020

@author: nils
"""


import asyncio
import websockets
import logging
import json

logger = logging.getLogger(__name__)

class WebSocketServer:
    
    def __init__(self, config):
        self.sid_to_socket = {}
        self.sid_to_room = {}
        self.room_to_sids={}
        
        self.active = True
        self.on_connect_callback = None
        self.on_disconnect_callback = None
        self.on_message_callbacks={}
        self.config = config
        
        
    def __socket_hash(self, socket):
        (ip, port) = socket.remote_address
        return self.__socket_hash_str(ip, port)
        
    def __socket_hash_str(self, ip:str, p:int):
        parts = ip.split(".")
        return self.__socket_hash_num(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), p)
        
    def __socket_hash_num(self, w, x, y, z, p):
        return 1099511627776*w + 4294967296*x + 16777216*y + 65536*z + p
            
    
    
    async def main_loop(self, socket, path):
        
        sid = self.connect_socket(socket)
        
        if self.on_connect_callback is not None:
            await self.on_connect_callback(sid)
            
        while self.active:
            try:
                raw = await socket.recv()
                data = json.loads(raw)
                
                message = data[self.config.message_ident]
                payload = data[self.config.payload_ident] if self.config.payload_ident in data else None
                
                if message in self.on_message_callbacks:
                    logger.info(f"message {message} with payload {payload} sending to callback")
                    message_callback = self.on_message_callbacks[message]
                    await message_callback(sid, payload)
                else:
                    logger.info(f"message {message} with payload {payload} but no takers")
                
                
            except websockets.exceptions.ConnectionClosedOK:
                logger.info(f"disonnection {socket.remote_address} with sid {sid}")
                if self.on_disconnect_callback is not None:
                    await self.on_disconnect_callback(sid)
                self.disconnect_sid(sid)
                return
            
        self.disconnect_sid(sid)
        
        
    def connect_socket(self, socket):
        sid = self.__socket_hash(socket)
        logger.info(f"new connection {socket.remote_address} with sid {sid}")
        self.sid_to_socket[sid] = socket
        return sid
    
    def disconnect_sid(self, sid):
        self.leave_room(sid)
        del(self.sid_to_socket[sid])
        
           
    def on_connect(self, callback):
        self.on_connect_callback = callback
        
    def on_disconnect(self, callback):
        self.on_disconnect_callback = callback
        
    def on_message(self, message, callback):
        self.on_message_callbacks[message] = callback
        
    async def send(self, message: str, sid: int, payload = None):
        logger.info(f"send {message} to sid {sid} with payload {payload}")
        raw = self.create_raw_content(message, payload)
        
        if sid not in self.sid_to_socket:
            logger.warn(f"could not send message {message} as sid {sid} does not exist")
            return
        socket = self.sid_to_socket[sid]
        await socket.send(raw)

    async def broadcast(self, message: str, payload = None, room = None, except_sid:int = None):
        logger.info(f"broadcast {message} with payload {payload} to room {room} except sid {except_sid}")
        
        raw = self.create_raw_content(message, payload)

        sids = self.sid_to_socket.keys() if room is None else self.room_to_sids[room]
        if except_sid is not None:
            sids = list(filter(lambda other_sid: other_sid != except_sid and other_sid in self.sid_to_socket, sids))
        sockets = list(map(lambda sid: self.sid_to_socket[sid], sids))
        
        if (len(sockets) > 0):
            await asyncio.wait([socket.send(raw) for socket in sockets])
        
        
    def create_raw_content(self, message: str, payload = None):
        data = {}
        data[self.config.message_ident] = message
        if payload is not None: data[self.config.payload_ident] = payload
        return json.dumps(data)
    
        
    def join_room(self, sid, room):
        logger.info(f"join {sid} room {room}")
        if room not in self.room_to_sids:
            self.room_to_sids[room] = set()
        
        if sid in self.sid_to_room:
            self.leave_room(sid)
            
        self.room_to_sids[room].add(sid)
        self.sid_to_room[sid] = room

    def leave_room(self, sid):
        logger.info(f"leave room {sid}")
        if sid not in self.sid_to_room:
            return
        room = self.sid_to_room[sid]
        del(self.sid_to_room[sid])
        self.room_to_sids[room].remove(sid)
        
    
    def run(self):
        
        logger.info(f"starting server")
        start_server = websockets.serve(self.main_loop, self.config.host, self.config.port)        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        
        
        
        
        
