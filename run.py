import threading
import os,asyncio
from websockets.asyncio.server import serve
from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler

global INSTANCES
INSTANCES = 0

def handle_client(instance_number):    
    import subprocess
    global INSTANCES

    print("Launching instance "+str(instance_number))

    run_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"run.py"))

    process = subprocess.call(
        ["streamlit","run",run_path, "--server.port",str(8501+instance_number),"--server.headless","true"],
        shell=True
    )
    INSTANCES -= 1

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with additional properties and functions"""

    def translate_path(self, path):
        # Serve files relative to a specific directory
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.base_path, relpath)
        return fullpath

    def do_GET(self):
        global INSTANCES
        """Handle GET requests"""
        if self.path == "/":  # If user connects to root, serve a default HTML
            self.path = "/redirect_page.html"  # Redirect to index.html in your folder
            t = threading.Thread(target=handle_client, args=(INSTANCES,))
            t.start()
            INSTANCES += 1
        elif self.path == "/get_instances":
            self.send_response(200,f"{INSTANCES}")

        return super().do_GET()  # Then use normal behavior

class HTTPServer(BaseHTTPServer):
    """The main server"""

    def __init__(self, base_path, server_address, RequestHandlerClass=HTTPRequestHandler):
        self.base_path = base_path
        super().__init__(server_address, RequestHandlerClass)

async def main():
    web_dir = os.path.join(os.path.dirname(__file__), 'http_server')
    os.chdir(web_dir)  # Important: set current working dir for SimpleHTTPRequestHandler
    httpd = HTTPServer(web_dir, ("", 8080))
    print("Serving at http://localhost:8080")
    httpd.serve_forever()

# Launch the HTTP server
if __name__ == "__main__":
    asyncio.run(main())
