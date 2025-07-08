import streamlit as st

from scripts.init import init,check_docker
init() # Initialisation des variables de session
check_docker() #Vérification de l'état de docker

from scripts.home import home
from scripts.containers import ctn_page
from scripts.login import User,login_page,find_user,deserialize_perms
from scripts.admin_panel import admin_panel
from scripts.cookies import Cookies
from scripts.deconnection_handler import set_handler
from scripts.info_ports import ports_info_page

try:
    st.set_page_config(layout="wide")
except:
    pass

# Gestion des cookies
conn = Cookies()
rd = conn.read_cookies() # Lecture des cookies
if rd != None: # Si la recherche n'est pas vide
    search = find_user(rd.name,rd.password) # On essaie de se connecter avec le mot de passe)
    if search[0] != False: # Si le statut de la recherche est True
        st.session_state["user"] = User(search[1][0],search[1][1],deserialize_perms(search[1][2])) # On crée l'utilisateur et on l'enregistre
    else: # Si la connexion a échouée, on affiche un dialogue. Normalement cela n'arrive jamais, sauf si la base de données est corrompue ou a été supprimée
        @st.dialog("Erreur de connection automatique")
        def show_forced_deconnection():
            """Dialogue d'erreur de connection automatique"""
            st.error("Votre session pointe vers un compte qui n'existe plus, vous allez être déconnecté.")
            st.image(r"docker-py\img\error_500.gif")
            if st.button("OK"):
                conn.clear_cookies()
                st.rerun()
        show_forced_deconnection()
elif rd == None and st.session_state["user"] != None:
    conn.write_cookies(st.session_state["user"])

st.session_state["pages"] = [st.Page(home,title="Accueil",icon="🏠",default=True),
                             st.Page(ctn_page,title="Conteneurs",icon="📦"),
                             st.Page(login_page,title="Compte",icon="🔑"),
                             st.Page(admin_panel,title="Pannel d'administration",icon="🎛️"),
                             st.Page(ports_info_page,title="Services",icon="🌐")]

with st.sidebar:
    with st.container(height=75,border=True):
        col1,col2 = st.columns([0.2,0.8])
        img = r"docker-py\img\no_user.png" if st.session_state["user"] == None else r"docker-py\img\user.png"
        img = r"docker-py\img\admin.png" if st.session_state["user"] != None and st.session_state["user"].has_perm(-1) == True else img
        col1.image(img,use_container_width=True)
        col2.write(st.session_state["user"].name if st.session_state["user"] != None else "Non connecté")
    page = st.navigation(st.session_state["pages"])

page.run()
set_handler()