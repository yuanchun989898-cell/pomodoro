#!/usr/bin/env python3
"""番茄时钟本地服务 — 提供网页 + 系统级弹窗通知"""

import http.server
import subprocess
import os
import json
from socketserver import ThreadingMixIn

PORT = 8888
DIR = os.path.dirname(os.path.abspath(__file__))

NO_CACHE = 'no-store, no-cache, must-revalidate'


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', NO_CACHE)
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _read_notify_body(self):
        title = '🍅 番茄时钟'
        message = '时间到，请休息！'
        length = int(self.headers.get('Content-Length', 0))
        if length:
            try:
                data = json.loads(self.rfile.read(length))
                title = data.get('title', title)
                message = data.get('message', message)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        return title, message

    @staticmethod
    def _escape_applescript(value):
        return value.replace('\\', '\\\\').replace('"', '\\"')

    def _show_system_alert(self, title, message):
        # block until user clicks OK on system alert
        safe_title = self._escape_applescript(title)
        safe_message = self._escape_applescript(message)
        script = (
            f'display alert "{safe_title}" message "{safe_message}" '
            f'buttons {{"好"}} default button "好" as critical'
        )
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or 'unknown error').strip()
            print(f'⚠️ 系统弹窗失败: {err}')
            return False
        return True

    def _handle_notify(self):
        title, message = self._read_notify_body()
        ok = self._show_system_alert(title, message)
        self.send_response(200 if ok else 500)
        self.send_header('Content-Type', 'text/plain')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(b'ok' if ok else b'fail')

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(b'ok')
        elif self.path == '/notify':
            self._handle_notify()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/notify':
            self._handle_notify()
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


class ThreadingHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    with ThreadingHTTPServer(('', PORT), Handler) as httpd:
        print(f'🍅 番茄时钟服务已启动: http://localhost:{PORT}')
        print(f'   在浏览器打开上面的地址即可使用')
        print(f'   倒计时结束时会弹出系统级通知')
        print(f'   按 Ctrl+C 停止')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')
