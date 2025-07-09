import os
from time import sleep
import streamlit as st
import subprocess
import configparser

from streamlit import context

from constants import RUN_PATH

def check_docker():
    # Si docker n'est pas lancé, on le lance # TODO: A retravailler pour une version multi-plateforme
    if os.name == "nt":
        if b"Docker Desktop.exe" not in subprocess.check_output("tasklist"):
            error = True
            for i in range(5):
                if subprocess.run(st.session_state["docker_path"]) == 0:
                    error = False
                    break
                sleep(1)
            if error == True:
                docker_err_1,docker_err_2 = st.columns([0.9,0.1])
                docker_err_1.error("Docker n'a pas démarré. Si vous pensez qu'il y a un problème, veuillez contacter l'administrateur.\nVous pouvez essayer d'actualiser la page.")
                docker_err_2.button("🔁",on_click=st.rerun)
                st.stop()
    else:
        print("Unsupported OS")

def get_ip():
    import requests
    response = requests.get("https://api.ipify.org?format=texte")
    response.raise_for_status()
    ip = response.text
    return ip

def init():
    path = RUN_PATH("..", 'config.ini')

    config = configparser.ConfigParser()
    config.read(path)
    http_config = config["http"]
    docker_config = config["docker"]

    keys = {
        "pages": None,
        "cookies_manager": None,
        "docker_warning_shown": False,
        "docker_warning": None,
        "run_docker": False,
        "account": None,
        "user": None,
        "ip": context.ip_address if context.ip_address == "localhost" else get_ip(),
        "port": http_config["local_port"],
        "docker_path": docker_config["DOCKER_LOCATION"],
        "vite_port": http_config["vite_port"],
        "mc_port": http_config["minecraft_port"],
    }

    for key, value in keys.items():
        if key not in st.session_state:
            st.session_state[key] = value