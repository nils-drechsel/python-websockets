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
    
    def __init__(self):
        self.id_to_socket = {}
        self.id_to_room = {}
        self.room_to_ids={}
        
        self.active = True
        self.on_connect_callback = None
        self.on_disconnect_callback = None
        self.on_message_callbacks={}
        
        
    def __socket_hash(self, socket):
        (ip, port) = socket.remote_address
        return self.__socket_hash_str(ip, port)
        
    def __socket_hash_str(self, ip:str, p:int):
        parts = ip.split(".")
        return self.__socket_hash_num(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), p)
        
    def __socket_hash_num(self, w, x, y, z, p):
        return 1099511627776*w + 4294967296*x + 16777216*y + 65536*z + p
            
    
    
    async def main_loop(self, socket, path):
        id = self.__socket_hash(socket)
        logger.debug(f"new connection {socket.remote_address} with id {id}")
        self.id_to_socket[id] = socket
        if self.on_connect is not None:
            self.on_connect(id)
        while self.active:
            try:
                raw = await socket.recv()
                data = json.load(raw)
                
                message = data["msg"]
                payload = data["pl"]
                
                logger.debug(f"message {message} with payload {payload}")
                
                message_callback = self.on_message_callbacks[message]
                message_callback(id, payload)
                
            except websockets.exceptions.ConnectionClosedOK:
                logger.debug(f"disonnection {socket.remote_address} with id {id}")
                if self.on_disconnect is not None:
                    self.on_disconnect(id)
            
                return
            
        del(self.clients[id])
           
    def on_connect(self, callback):
        self.on_connect_callback = callback
        
    def on_disconnect(self, callback):
        self.on_disconnect_callback = callback
        
    def on_message(self, message, callback):
        self.on_message_callbacks[message] = callback
        
    async def send(self, message, id, payload = None, from_id = None):
        data = {"msg": message, "pl": payload} 
        if from_id is not None:
            data["id"] = from_id
        raw = json.dumps(data)
        socket = self.id_to_socket[id]
        await socket.send(raw)

    async def broadcast(self, message, payload = None, room = None, except_id = None, from_id = None):
        data = {"msg": message, "pl": payload}
        if from_id is not None:
            data["id"] = from_id
        raw = json.dumps(data)

        ids = self.id_to_socket.keys() if room is None else self.room_to_ids[room]
        if except_id is not None:
            ids = list(filter(lambda client: client != except_id, ids))
        sockets = list(map(lambda id: self.id_to_socket[id], ids))
            
        await asyncio.wait([socket.send(raw) for socket in sockets])
        
    def join_room(self, id, room):
        if room not in self.room_to_ids:
            self.room_to_ids[room] = set()
        
        if id in self.id_to_room:
            self.leave_room(id)
            
        self.room_to_ids[room].add(id)
        self.id_to_room[id] = room

    def leave_room(self, id):
        if id not in self.id_to_room:
            return
        room = self.id_to_room[id]
        del(self.id_to_room[id])
        self.room_to_ids[room].remove(id)
    
    def run(self):
        start_server = websockets.serve(self.main_loop, "localhost", 8765)        
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        
        
        
        
        
