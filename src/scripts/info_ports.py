import streamlit as st

def ports_info_page():
    user = st.session_state["user"]
    
    ip = st.session_state["ip"]

    st.title("Informations sur les ports")
    st.write("Cette page affiche les informations sur les ports des conteneurs.")
    
    st.divider()
    
    st.write(f"Comme vous le savez, ce site s'affiche sur {ip}:{st.session_state['port']}")

    st.divider()

    st.write(f"Le serveur minecraft se rejoint par {ip}:{st.session_state['mc_port']}")

    st.divider()

    st.write(f"Et finalement portainer se rejoins sur {ip}:30300.")
    st.info("Ceci dit, vous n'avez aucun besoin d'aller voir ce site, il ne vous sera d'aucune utilité, et vous n'avez pas les autorisations")

    if user is not None and user.has_perm(-1):
        st.divider()

        st.write("Le port 30000 sert pour le serveur websocket")