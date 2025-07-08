import streamlit.components.v1 as components
from streamlit import session_state,write

from logger.component.logger import Server
from logger.component.logger import ViteServer
import threading

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
        distant = f"http://localhost:3001"
    else:
        distant = f"http://{ip}:{session_state['vite_port']}"
    write(distant)
    components.iframe(distant, height=800)
    t.join()
    print("Thread terminated")
