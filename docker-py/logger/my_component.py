import streamlit.components.v1 as components
from streamlit import session_state

from logger.component.logger import Server
from logger.component.logger import ViteServer
import threading,psutil

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

# Fonction Python pour appeler le composant
def log_viewer(ctn):
    def start_ws():
        vite = ViteServer(3001)
        vite.start()
        server = Server(ctn)
        server.run_server()
        vite.stop()

    t = threading.Thread(target=start_ws, daemon=True)
    t.start()
    ip = session_state["ip"]
    if ip == "localhost":
        components.iframe(f"http://localhost:3001", height=800)
    else:
        print(f"http://{ip}:{session_state['vite_port']}")
        components.iframe(f"http://{ip}:{session_state['vite_port']}", height=800)
    t.join()
    print("Thread terminated")
