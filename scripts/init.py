import streamlit as st
import os, subprocess

#Si docker n'est pas lancé, on le lance
subprocess.Popen(r'"C:\Program Files\Docker\Docker\Docker Desktop.exe"') if "Docker Desktop.exe" not in os.popen('tasklist').read() else None

def init():
    keys = {"pages":None,
            "cookies_manager":None,
            "docker_warning_shown":False,
            "docker_warning":None,
            "run_docker":False,
            "account":None,
            "user":None,
            "messages":[]}

    for key, value in keys.items():
        if key not in st.session_state:
            st.session_state[key] = value

