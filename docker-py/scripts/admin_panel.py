from typing import Iterable
import streamlit as st
from scripts.login import (
    User,
    find_admin,
    pass_admin,
    find_user,
    serialize_perms,
    BASE_PERMS,
)
from scripts.db_manager import Interface
import json


def save_perms(db: Interface, user: tuple, *perms):
    """
    Écriture des permissions données sous *perms tel que
    """
    # Si les permissions sont dans un set, l'extraire
    if len(perms) == 1:
        perms = perms[0]
    # Écriture des permissions avec une sérialisation des objets
    name = user[0]
    permissions = json.dumps(perms)
    db.update((f"name {name}",), (f"permissions {permissions}",))
    st.toast("Les permissions ont bien été sauvegardées")


@st.dialog("Créer un utilisateur", width="large")
def create_user(db):
    """
    Dialogue de création d'utilisateur
    """

    def create_user(name, password, perms: Iterable):
        """
        Écriture du nouvel utilisateur
        """
        # Si la raison de l'échec de find_user n'est pas nom d'utilisateur incorrect (soit mot de passe incorrect soit mot de passe bon), alors l'utilisateur existe, la fonction retourne False
        if find_user(name, password)[1] != "Nom d'utilisateur incorrect":
            return False
        # Sinon, on crée l'utilisateur et on retourne True
        else:
            db.write([name, password, serialize_perms(perms)])
            return True

    # Formulaire
    with st.form(key="create user"):
        name = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Créer l'utilisateur"):
            # Si l'utilisateur existe, on affiche un toast
            st.toast("Nom d'utilisateur deja pris", icon="❌") if create_user(
                name, password, BASE_PERMS
            ) is False else None
            st.rerun()


def admin_panel():
    """
    Page du panneau de contrôle
    """

    # Création de l'interface avec la Database sqlite3 (voir db_manager.py)
    db = Interface("users", ["name text", "password text", "permissions text"])

    with db.db:  # On utilise le Delta Generator pour fermer automatiquement la base de données à la fin de son utilisation
        # On récupère l'utilisateur connecté
        user = st.session_state["user"]
        st.title("Panel d'administration")

        if user is not None:  # Si l'utilisateur est connecté
            # On vérifie ses permissions
            if user.has_perm(-1):
                st.header("Bienvenue, {}".format(user.name))
                st.divider()
                # On affiche les utilisateurs et leurs permissions sous forme de data editor
                users = db.read()

                for t_user in users:
                    name_col, perm_col, button_col = st.columns([0.3, 0.65, 0.05])  # On peut décider de la taille des colonnes
                    name_col.metric("Nom d'utilisateur", t_user[0])

                    show_password = name_col.segmented_control("Afficher le mdp",["Oui", "Non"],key="show_password_" + t_user[0],default="Non",)
                    if show_password == "Oui":
                        name_col.write(t_user[1])
                    dte = perm_col.data_editor(json.loads(t_user[2]), key="save_" + t_user[0])
                    button_col.button("💾",help="Sauvegarder",on_click=save_perms,args=(db,t_user,dte,),key="save_" + str(t_user),)  # Bouton de sauvegarde, appelant save_perms

                    st.divider()

                # Fonction appelant le dialogue create_user
                st.button("Créer un utilisateur", on_click=create_user, args=(db,))
            else:
                # Si l'utilisateur n'a pas les permissions
                st.error(
                    "Vous n'avez pas les permissions requises. Si vous pensez que c'est une erreur, contactez l'administrateur"
                )
        else:  # Si l'utilisateur n'est pas connecté
            st.error(
                "Vous n'êtes pas connecté. Le panel a besoin de permissions spéciales"
            )
        # Si aucun administrateur n'a encore ete crée, on propose à l'utilisateur actuel de devenir administrateur
        if len(find_admin()) == 0:
            no_admin_col1, no_admin_col2 = st.columns([0.9, 0.1])
            no_admin_col1.info("Aucun administrateur n'a encore ete crée. Voulez vous devenir un administrateur?")
            no_admin_col2.button("Oui", on_click=become_admin, args=(user,))


@st.dialog("Devenir administrateur")
def become_admin(user):
    """
    Dialogue de création d'un admin
    """
    if user is not None:  # Si l'utilisateur est connecté
        st.info(f"{user.name} va devenir administrateur. Confirmer?")
        if st.button("Confirmer"):
            pass_admin(user)
    else:  # Si l'utilisateur n'est pas connecté
        st.error("Connectez vous ou créez un compte.")
        st.page_link(st.session_state["pages"][2], label="Page de connection", icon="↗")
