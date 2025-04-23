import streamlit.components.v1 as components
import streamlit as st

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
    components.iframe("http://localhost:3001", height=800)
    t.join()
    print("Thread terminated")