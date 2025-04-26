import threading
import os,asyncio
from websockets.asyncio.server import serve
from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler

global INSTANCES
INSTANCES = []

def handle_client():    
    import subprocess
    global INSTANCES

    instance_number = len(INSTANCES)
    if instance_number >= 9:
        print("Maximum number of instances reached")
        return

    print("Launching instance "+str(instance_number))

    run_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"run.py"))


    process = subprocess.Popen(
        ["streamlit","run",run_path, "--server.port",str(8501+instance_number),"--server.headless","true","--",str(instance_number)],
        shell=True
    )
    INSTANCES.append(str(instance_number))

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
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.path = "/redirect_page.html"  # Redirect to index.html in your folder
            t = threading.Thread(target=handle_client)
            t.start()
            return super().do_GET()
        elif self.path == "/get_instances":
            self.send_response(200)
            self.send_header('Content-type','int')
            self.end_headers()
            self.wfile.write(str(INSTANCES).encode())
            return
        else:
            return super().do_GET()  # Then use normal behavior

    def do_POST(self):
        """Handle POST requests"""
        global INSTANCES
        
        if self.path == "/disconnect":
            content_length = int(self.headers['Content-Length'])  # Taille des données reçues
            post_data = self.rfile.read(content_length)  # Lecture des données brutes

            # Suppose qu'on reçoit juste un numéro d'instance
            instance_number = int(post_data.decode())

            # Arrêter proprement le serveur Streamlit correspondant
            process = INSTANCES.pop(instance_number)
            if process:
                process.terminate()
                print(f"Stopped instance {instance_number}")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Disconnected OK")

        else:
            self.send_response(404)
            self.end_headers()

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

