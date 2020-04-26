#!/usr/bin/env python3

import os
import http.server
import socketserver

PORT = 8000

web_dir = os.path.join(os.path.dirname(__file__), 'public')
os.chdir(web_dir)

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()