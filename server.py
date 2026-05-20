#!/usr/bin/env python3
"""番茄时钟本地服务 — 提供网页 + 系统级弹窗通知"""

import http.server
import subprocess
import os
import threading

PORT = 8888
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        if self.path == '/notify':
            # block until user clicks OK on system alert
            subprocess.run([
                'osascript', '-e',
                'display alert "🍅 番茄时钟" message "时间到，请休息！" as critical'
            ])
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    with http.server.HTTPServer(('', PORT), Handler) as httpd:
        print(f'🍅 番茄时钟服务已启动: http://localhost:{PORT}')
        print(f'   在浏览器打开上面的地址即可使用')
        print(f'   倒计时结束时会弹出系统级通知')
        print(f'   按 Ctrl+C 停止')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')
