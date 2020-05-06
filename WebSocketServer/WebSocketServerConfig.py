#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 11:17:21 2020

@author: nils
"""


class WebSocketServerConfig:
    
    def __init__(self):
        self.port = 8765
        self.host = "127.0.0.1"
        self.message_ident = "m"
        self.payload_ident = "p"
