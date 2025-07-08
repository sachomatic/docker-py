import websockets
import socket
import threading
import asyncio
import datetime
import random
import traceback
import psutil
from dateutil import parser

def clean_ansi(log):
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', log)

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

def get_local_ip():
    # Create a temporary socket to connect to an external server
    # This will allow us to retrieve the correct local IP used for communication
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # Connect to an external IP (Google's public DNS server)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception as e:
            print("Error retrieving local IP:")
            traceback.print_exception(e)

class ViteServer:
    def __init__(self, port=3001):
        self.port = port
        self.process = None

    def start(self):
        import subprocess
        import time
        import os
        print(f"Starting Vite server on port {self.port}")
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
        print(path)
        self.process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=path,
            shell=True
        )
        time.sleep(2)  # wait for server to boot

    def stop(self):
        if self.process:
            print("Stopping Vite server")
            kill_process_tree(self.process.pid)
            self.process.wait()
        else:
            print("Server not running")

class Logger(threading.Thread):
    def __init__(self, container):
        super().__init__()
        self.logs = []
        self.container = container

        self.loop = asyncio.new_event_loop()

        started_at = container.attrs['State']['StartedAt']
        start_time = int(parser.isoparse(started_at.strip('"')).timestamp())

        logs = container.logs(since=start_time)
        for line in logs.splitlines():
            decoded_line = line.decode('utf-8')
            self.logs.append(clean_ansi(decoded_line))

    def run(self):
        print("Logger initialized")
        self.task = self.loop.run_in_executor(None, self._logger)

    def _logger(self):
        import time
        while True:
            start_time = int(datetime.datetime.now().timestamp())
            logs = self.container.logs(since=start_time)
            for line in logs.splitlines():
                decoded_line = line.decode('utf-8')
                self.logs.append(clean_ansi(decoded_line))
            time.sleep(1)

    def stop(self):
        self.task.cancel()
        self.loop.stop()
        self.join()

class Server(threading.Thread):
    def __init__(self, container):
        super().__init__()
        self.name = f"Server thread {random.randint(0, 1000)}"
        self.Logger = Logger(container)
        self.Logger.start()

        # Créer et assigner une event loop dans le thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def handle_client(self,websocket):
        print("Client connected")
        try:
            async for message in websocket:  # Loop to handle multiple messages
                if message == "get_logs":
                    if self.Logger.logs != []:
                        while self.Logger.logs:
                            line = self.Logger.logs.pop(0)
                            await websocket.send(line)
                            print("Sent: " + line)
                    else:
                        await websocket.send("NO_CONTENT")
                else:
                    await websocket.send("BAD_REQUEST")

        except websockets.ConnectionClosed:
            print("Client disconnected")            
        except asyncio.exceptions.CancelledError:
            print("Cancelled")
        finally:
            self.stop()

    async def start_server(self):
        self.serv = await websockets.serve(self.handle_client, "localhost", 8081)
        await self.serv.wait_closed()

    def run_server(self):
        print("Server initialized")
        self.server_task = self.loop.create_task(self.start_server())
        try:
            self.loop.run_until_complete(self.server_task)
        except KeyboardInterrupt:
            self.stop()
        except RuntimeError:
            pass

        

    def stop(self):
        #Stop the Logger
        print("Stopping Logger")
        self.Logger.stop()

        #Close the server
        print("Closing websocket server")
        self.serv.close()
        asyncio.create_task(self.serv.wait_closed())

        #Close all pending task
        print("Cancelling pending tasks")
        for task in asyncio.all_tasks(loop=self.loop):
            print("Cancelling "+task.get_name())
            task.cancel()
        self.loop.stop()
        
        print("exiting on ",self.name)