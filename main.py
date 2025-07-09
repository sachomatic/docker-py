from configparser import ConfigParser
import os
import subprocess
from typing import TypedDict
import psutil
from pynput.keyboard import Listener, KeyCode
import asyncio
from aiohttp import web, ClientSession, WSMsgType
from aiohttp.web_request import Request
import aiohttp
import time
import uuid
import socket

class Instance(TypedDict):
    port: int
    pid: int
    last: float

instances: dict[str, Instance] = {} 

config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
config_http = config["http"]

PROXY_PORT = config_http.getint("proxy_port", 8080)
LOCAL_BASE_PORT = config_http.getint("local_ports", 3300)
MAX_INSTANCES = config_http.getint("max_instances", 3)
INACTIVITY_TIMEOUT = config_http.getint("inactivity_timeout", 60)

async def wait_for_streamlit_port(port, host="127.0.0.1", timeout=10):
    """Attend que le port soit ouvert (Streamlit prêt)"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            await asyncio.sleep(0.2)
    return False

async def launch_streamlit(user_id: str):
    port = LOCAL_BASE_PORT + len(instances)
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "handler.py"))
    cmd = f'streamlit run "{file_path}" --server.port {port} --server.headless true'
    proc = subprocess.Popen(cmd, shell=True)
    instances[user_id] = {"port": port, "pid": proc.pid, "last": time.time()}
    # Attendre que le port soit ouvert
    ok = await wait_for_streamlit_port(port)
    if not ok:
        print(f"Erreur : Streamlit sur le port {port} n'a pas démarré à temps.")
    return port

async def proxy_handler(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id or user_id not in instances:
        user_id = str(uuid.uuid4())
        port = await launch_streamlit(user_id)
    else:
        port = instances[user_id]["port"]
        instances[user_id]["last"] = time.time()

    # Proxy la requête vers l'instance Streamlit
    url = f"http://127.0.0.1:{port}{request.rel_url}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    
    if request.headers.get("upgrade", "").lower() == "websocket":
        ws_server = web.WebSocketResponse()
        await ws_server.prepare(request)
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws_client:
                async def ws_forward(ws_from, ws_to):
                    async for msg in ws_from:
                        if msg.type == WSMsgType.TEXT:
                            await ws_to.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_to.send_bytes(msg.data)
                        elif msg.type == WSMsgType.CLOSE:
                            await ws_to.close()
                await asyncio.gather(
                    ws_forward(ws_server, ws_client),
                    ws_forward(ws_client, ws_server)
                )
        return ws_server
    else:
        # Proxy HTTP classique
        async with ClientSession() as session:
            data = await request.read()
            async with session.request(
                request.method, url, headers=headers, data=data, allow_redirects=False
            ) as resp:
                body = await resp.read()
                response = web.Response(body=body, status=resp.status, headers=resp.headers)
        response.set_cookie("user_id", user_id)
        return response

async def cleanup_instances():
    while True:
        now = time.time()
        for user_id, info in list(instances.items()):
            if now - info["last"] > INACTIVITY_TIMEOUT:
                try:
                    os.kill(info["pid"], 9)
                except Exception:
                    pass
                del instances[user_id]
        await asyncio.sleep(30)

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
        map(kill_process_tree, (instance["pid"] for instance in instances.values()))
        os._exit(0)

    def on_press(key):
        if isinstance(key, KeyCode) and key.char == '\x04':  # Ctrl+D is ASCII 4
            close()

    listener = Listener(on_press=on_press)
    listener.start()
    print("Server running, press Ctrl+D to stop")
    return listener

app = web.Application()
app.router.add_route('*', '/{tail:.*}', proxy_handler)

if __name__ == "__main__":
    listener = exit_thread()
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_instances())
    web.run_app(app, port=PROXY_PORT)
    listener.join()