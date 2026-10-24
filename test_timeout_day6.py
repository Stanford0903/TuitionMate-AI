
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen
from urllib.error import URLError


class SlowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(2)

        try:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionAbortedError):
            pass

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 0), SlowHandler)
port = server.server_address[1]

thread = threading.Thread(
    target=server.serve_forever,
    daemon=True
)
thread.start()

try:
    with urlopen(
        f"http://127.0.0.1:{port}",
        timeout=0.2
    ) as response:
        print("FAIL | Expected timeout")
except (TimeoutError, URLError) as error:
    print("PASS | Slow service timeout detected")
    print("Error type:", type(error).__name__)
finally:
    server.shutdown()
    server.server_close()
