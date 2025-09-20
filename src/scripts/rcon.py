from rcon.source import Client
import streamlit as st

def send_command(command,args):
    with Client(st.session_state["ip"], 25575) as client:
        response = client.run(command)
    return response

@st.dialog("RCON")
def commands_dialog():
    messages = st.container()
    if prompt := st.chat_input("Command"):
        cmd,args = prompt.split(" ",1)
        messages.chat_message("user").write(prompt)
        response = send_command(cmd,args)
        messages.chat_message("assistant").write(response)