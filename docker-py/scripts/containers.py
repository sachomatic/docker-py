import streamlit as st
from scripts.login import BASE_USER
import docker.errors as de
from docker.models.containers import Container
from docker import DockerClient
import subprocess
import re

@st.dialog(title="Que se passe t-il?", width="large")
def info():
    """
    Un dialogue qui explique à l'utilisateur pourquoi la page ne se charge pas immédiatement
    """
    st.info("Cette page lance docker au démarrage, cela peut prendre du temps. ")
    st.error(
        "Si Docker n'est pas lancé au bout de quelques minutes, il y a peut être un problème. Vous pouvez essayer d'actualiser la page. Si le problème persiste, veuillez contacter l'administrateur."
    )


while True:
    # Attente du client docker
    try:
        client = DockerClient(base_url="npipe:////./pipe/docker_engine")
        break
    except de.DockerException:
        # En attendant, on affiche un message d'explication
        if st.session_state["docker_warning"] is None:
            col1, col2 = st.columns([0.9, 0.1])
            st.session_state["docker_warning"] = (
                col1.info("En attente du client Docker..."),
                col2.button("?", on_click=info),
            )


def launch_compose():
    """
    Lance le docker-compose.yml (et arrête les conteneurs existants)
    """
    import os

    for container in client.containers.list():
        st.toast("Arrêt de {}".format(container.name))
        container.stop()
    os.system("docker compose up -d")

@st.dialog("Résultat")
def show(output):
    output = re.sub(r'\x1b\[[0-9;]*m', '', output)
    st.write(output)

def mc_exec(command,id):
    """
    Exécuter une commande sur le conteneur minecraft
    """
    st.toast("Commande envoyée")
    result = subprocess.run(f"docker exec {id} rcon-cli {command}",capture_output=True, text=True, shell=True)
    show(result.stdout)

def ctn_page():
    """
    Page des conteneurs
    """

    st.title("Conteneurs")
    # Obtention d'une liste de conteneurs
    # * On force le type-checker à accepter que containers soit du type `list[Container]`
    containers: list[Container] = list(client.containers.list(all=True))
    # Vérification des permissions de l'utilisateur
    if st.session_state["user"] is None:
        st.info("Vous n'êtes pas connecté, donc vous avez les permissions de base.")

    # Si l'utilisateur n'est pas connecté, un User avec les base_perm est crée
    user = st.session_state["user"] if st.session_state["user"] != None else BASE_USER

    # Bouton pour lancer le compose
    st.divider()
    but_col, help_col = st.columns([0.2, 0.8])
    but_col.button("Lancer le compose",on_click=launch_compose,key="launch_compose",disabled=False if user.has_perm(1) and user.has_perm(2) else True,)
    help_col.info("Le docker-compose.yml lance (redémarre si les containers sont déjà lancés) tous les services nécessaires pour le serveur minecraft. C'est la méthode conventionnelle." \
    "Notez cependant que le serveur prends du temps à démarrer, cela peut prendre quelques minutes.",)
    st.divider()

    # Affichage des conteneurs
    for container in containers:
        with st.container():
            # Voit si le conteneur peut être démarré
            start_disabled = True if not user.has_perm(1) else False
            start_help = None if user.has_perm(1) else "Vous n'avez pas les permissions requises"

            # Voit si le conteneur peut être arrêté
            stop_disabled = True if not user.has_perm(2) or container.status != "running" else False
            stop_help = "Le conteneur n'est pas en cours d’exécution" if container.status != "running" else None
            stop_help = "Vous n'avez pas les permissions requises" if not user.has_perm(2) else stop_help

            st.write("Nom du conteneur : ", container.name)
            st.badge(
                "Statut : " + container.status,
                color="green" if container.status == "running" else "red",
            )
            st.write("ID du conteneur : ", container.id)

            # Création des colonnes pour les logs, le démarrage et l'arrêt respectivement. On attribue à chacun une clé pour éviter les conflits
            b_col_1, b_col_2, b_col_3 = st.columns(3)
            if b_col_1.button("Voir les logs", key="logs" + container.id): # type: ignore # Le module ne définit pas les types
                see_logs(container)
            if b_col_2.button("Lancer le conteneur",key="start" + str(container.id), disabled=start_disabled,help=start_help,):
                container.start()
                st.rerun()
            if b_col_3.button("Arrêter le conteneur",key="stop" + str(container.id), disabled=stop_disabled,help=stop_help,):
                stop(container)
            if container.name == "mc_docker-mc-1" and user.has_perm(-1):
                cmd_col1, cmd_col2 = st.columns([0.8,0.2],vertical_alignment="bottom")
                cmd = cmd_col1.text_input("Commande",key="mc_cmd")
                cmd_col2.button("Exécuter",key="mc_exec",on_click=mc_exec,args=(cmd,container.id))
        st.divider()


@st.dialog(title="Arrêter le conteneur?")
def stop(container):
    """
    Dialogue demandant à l'utilisateur de confirmer l'arrêt
    """
    st.warning(
        "Voulez-vous vraiment arrêter le conteneur ? Assurez vous d'avoir sauvegardé les données du conteneur."
    )
    if st.button(f"Arrêter {container.name}"):
        container.stop()
        st.rerun()


@st.dialog(title="Logs du conteneur", width="large")
def see_logs(ctn):
    """
    Import du component customisé
    """
    from logger.my_component import log_viewer

    log_viewer(ctn)
