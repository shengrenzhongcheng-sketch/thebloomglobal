import os
import sys
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import webbrowser

PORT = 8088
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class RangeHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def translate_path(self, path):
        path = path.split('?', 1)[0].split('#', 1)[0]
        rel_path = os.path.normpath(path.lstrip('/'))
        full_path = os.path.join(DIRECTORY, rel_path)
        if os.path.isdir(full_path):
            full_path = os.path.join(full_path, 'index.html')
        return full_path

    def do_GET(self):
        file_path = self.translate_path(self.path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, "File Not Found")
            return

        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        range_header = self.headers.get('Range')
        if range_header:
            try:
                ranges = range_header.replace('bytes=', '').split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(length))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, must-revalidate')
                self.end_headers()

                with open(file_path, 'rb') as f:
                    f.seek(start)
                    chunk_size = 256 * 1024
                    remaining = length
                    while remaining > 0:
                        to_read = min(remaining, chunk_size)
                        buf = f.read(to_read)
                        if not buf:
                            break
                        self.wfile.write(buf)
                        remaining -= len(buf)
                return
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                # Browser aborted previous seek connection; normal behavior
                return
            except Exception as e:
                return

        # Full 200 response
        try:
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
            self.end_headers()

            with open(file_path, 'rb') as f:
                chunk_size = 256 * 1024
                while True:
                    buf = f.read(chunk_size)
                    if not buf:
                        break
                    self.wfile.write(buf)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return

    def log_message(self, format, *args):
        # Suppress noisy standard request logging
        pass

def run():
    server_address = ('127.0.0.1', PORT)
    httpd = ThreadingHTTPServer(server_address, RangeHTTPRequestHandler)
    print(f"==================================================")
    print(f" WebBloom Multi-Threaded Range Server Running!")
    print(f" URL: http://127.0.0.1:{PORT}/index.html")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    run()
