import threading
import os,asyncio
from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler
import psutil
import subprocess
import json
import configparser
from pynput.keyboard import Listener, KeyCode

def get_ip():
    import requests
    response = requests.get("https://api.ipify.org?format=texte")
    response.raise_for_status()
    ip = response.text
    return ip

lock = threading.Lock()

run_dir = os.path.abspath(os.path.dirname(__file__))

config = configparser.ConfigParser()
config.read(run_dir+'\\config.ini')

switch = config["switch"]["USE"]
server = config["http_server"]
ports = config["port_set"+str(switch)]

MAX_INSTANCES = int(server["MAX_INSTANCES"])
SERVER_BASE_PORT = int(ports["HTTP_LOCAL_BASE_PORT"])
CLIENT_BASE_PORT = int(ports["HTTP_CLIENT_BASE_PORT"])
ACCESS_PORT = int(ports["HTTP_ACESS_PORT"])
IP = server["IP"] if server["IP"] != "None" else get_ip()
INSTANCE_LOCK = threading.Lock()


instances = {}  # id -> process

k = Listener()

def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print(f"Process with PID {pid} does not exist.")
        return

    for child in parent.children(recursive=True):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass  # déjà mort, pas grave

    try:
        parent.kill()
    except psutil.NoSuchProcess:
        pass  # lui aussi peut déjà être mort

def exit_thread():
    def close():
        #set_trace()
        print("Closing server")
        if len(instances) > 0:
            for instance in instances.keys():
                kill_process_tree(instances[instance])
        os._exit(0)

    def on_press(key):
        if isinstance(key, KeyCode) and key.char == '\x04':  # Ctrl+D is ASCII 4
            close()

    listener = Listener(on_press=on_press)
    listener.start()
    print("Server running, press Ctrl+D to stop")
    return listener

def find_available_id():
    for i in range(0,MAX_INSTANCES):
        if i not in instances:
            return i
    return None

def handle_client():
    with INSTANCE_LOCK:
        instance_id = find_available_id()
        if instance_id is None:
            print("Maximum number of instances reached")
            return None

        port = SERVER_BASE_PORT + instance_id
        print(f"Launching instance {instance_id} on port {port}")

        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),"docker-py", "handler.py"))
        command = f'cd "{run_dir}" && streamlit run "{file_path}" --server.port {port} --server.headless true'
        process = subprocess.Popen(
            command,
            shell=True
        )
        instances[instance_id] = process.pid
        return instance_id

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with additional properties and functions"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/":
            instance_id = handle_client()
            if instance_id is not None:
                # Send a small HTML that redirects the user
                self.send_response(302)
                self.send_header('Location', f"http://{IP}:{CLIENT_BASE_PORT + instance_id}")
                self.end_headers()
            else:
                self.send_response(503)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Desole, il y a trop d'utilisateurs concurrents sur le site. Veuillez reessayer plus tard.")
        else:
            return super().do_GET()  # Then use normal behavior

    def do_POST(self):
        """Handle POST requests"""
        
        if self.path == "/disconnect":
            content_length = int(self.headers['Content-Length'])  # Taille des données reçues
            post_data = self.rfile.read(content_length)  # Lecture des données brutes

            try:
                response = json.loads(post_data.decode())
                instance_id = int(response[list(response.keys())[0]])-1
                with INSTANCE_LOCK:
                    pid = instances.pop(instance_id, None)
                if pid:
                    kill_process_tree(pid)
                    print(f"Stopped instance {instance_id}")
                    self.send_response(200)
                    origin = self.headers.get("Origin")
                    if origin and "localhost" in origin:
                        self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Access-Control-Allow-Credentials", "true")
                    self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "*")
                    self.end_headers()
                    self.wfile.write(b"Disconnected OK")
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Instance not found")
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                print("Error:", e)
                self.wfile.write(f"Invalid request: {e}".encode())
            

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        origin = self.headers.get("Origin")
        if origin and "localhost" in origin:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

class HTTPServer(BaseHTTPServer):
    """The main server"""

    def __init__(self, base_path, server_address, RequestHandlerClass=HTTPRequestHandler):
        self.base_path = base_path
        super().__init__(server_address, RequestHandlerClass)

async def main():
    listener = exit_thread()
    web_dir = os.path.join(os.path.dirname(__file__), "docker-py" ,'http_server')
    os.chdir(web_dir)  # Important: set current working dir for SimpleHTTPRequestHandler
    httpd = HTTPServer(web_dir, ("", 8080))
    print(f"Serving at http://{IP}:{ACCESS_PORT}")
    httpd.serve_forever()
    listener.join()

# Launch the HTTP server
if __name__ == "__main__":
    with lock:
        asyncio.run(main())