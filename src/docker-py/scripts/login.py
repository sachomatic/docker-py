from typing import Iterable, Literal
import streamlit as st
import time
import json
from scripts.db_manager import Interface
from threading import Lock


class Permission():
    """Classe des permissions"""

    def __init__(self, name: str, value: bool):
        self.name = name
        self.value = value

class User:
    """Classe utilisateur"""

    def __init__(self, name: str, password: str, perms: Iterable[Permission]):
        self.name = str(name)
        self.password = str(password)
        self.perms = list(perms)

    def is_admin(self):
        """Retourne True si l'utilisateur est admin"""
        return self.perms[-1].value

    def has_perm(self, index: int):
        """Retourne True si l'utilisateur a la permission ou si il est administrateur"""
        return self.perms[index].value is True or self.is_admin()



# Création d'une interface avec interface.db (j'aurais du changer le nom quand je le pouvais)
db = Interface("users", ["name text", "password text", "permissions text"])

# Les permissions de base
BASE_PERMS = ( # Elles sont par ordre de priorité
    Permission("See logs", True),
    Permission("Start containers", False),
    Permission("Stop containers", False),
    Permission("Admin panel", False),
    Permission("Admin", False),
)

# Utilisateur de base
BASE_USER = User("utilisateur", "password", BASE_PERMS)


@st.dialog("Déconnexion")
def logout_dialog():
    """Dialogue de déconnexion"""

    st.warning("Voulez-vous vraiment vous déconnecter ?")
    if st.button("Se déconnecter"):
        logout()  # Déconnexion


@st.dialog("Changer le mot de passe")
def change_password_dialog():
    """Dialogue de changement de mot de passe"""

    new_password = st.text_input("Nouveau mot de passe", type="password")
    if st.button("Changer le mot de passe"):
        db.update((f"name {st.session_state['user'].name}",), (f"password {new_password}",))
        st.session_state["user"].password = new_password
        from scripts.cookies import Cookies

        Cookies().clear_cookies()
        st.success("Mot de passe modifié", icon="✅")
        time.sleep(2)
        st.rerun()


def logout():
    """Effaçage des variables de session de l'utilisateur et de ses cookies"""

    from scripts.cookies import Cookies

    conn = Cookies()  # Gestionnaire de cookies
    st.session_state["user"] = None  # Effacement des variables de session
    conn.clear_cookies()  # Effacement des cookies
    st.rerun()


lock = Lock()  # On utilise un verrou (Lock) pour empêcher l'utilisation concurrente de la base de données
with db.db:
    def find_admin():
        """Retourne tous les administrateurs présents dans la base de données"""

        with lock:
            users = db.read([])  # Récupère toutes les lignes (dans ce cas tous les utilisateurs)
        users_with_admin = []
        for user in users:
            permissions = json.loads(user[2])  # Les permissions sont stockées à la troisième position
            if permissions[-1]["value"] is True:  # Si la dernière permission (admin) est True
                users_with_admin.append(user)  # On ajoute l'utilisateur à la liste
        return users_with_admin

    def find_user(name: str, password: str):
        """Retourne le statut de la recherche et l'utilisateur si la recherche réussit"""

        with lock:
            users: list[list] = db.read([["name", name]])  # Récupère l'utilisateur par son nom
        if len(users) == 0:  # Si aucun utilisateur ne correspond, on retourne False
            return (False, "Nom d'utilisateur incorrect")
        for user in users:
            if user[1] == password:  # Si le mot de passe correspond, on retourne le statut de la recherche et l'utilisateur
                return (True, user)
            else:  # Sinon, on retourne False et "Mot de passe incorrect"
                return (False, "Mot de passe incorrect")
        raise RuntimeError

    def pass_admin(user):
        """Écrit la permission admin sur l'utilisateur donné"""

        # Extraction des permissions
        perms = find_user(user.name, user.password)[1][2]
        perms = json.loads(perms)
        permissions_objs = [Permission(perm["name"], perm["value"]) for perm in perms]

        # On change la dernière permission (admin) à True
        permissions_objs[-1].value = True

        # On sérialise les permissions
        perms_dict = [{"name": perm.name, "value": perm.value} for perm in permissions_objs]

        with lock:
            db.update((f"name {user.name}",), (f"permissions {json.dumps(perms_dict)}",))  # On mets les permissions à jour

        st.balloons()
        st.toast("Bravo, vous êtes maintenant administrateur. Mise à jour...", icon="✅")  # On affiche un toast
        st.session_state["user"].perms[-1].value = True  # On change les variables de session
        st.rerun()

    def serialize_perms(perms):
        """Transforme les objets Permission en string de dictionnaire"""
        perms_dict = [{"name": perm.name, "value": perm.value} for perm in perms]
        return json.dumps(perms_dict)

    def deserialize_perms(raw_perms: str):
        """Transforme les string de dictionnaire en objets Permission"""
        perms = json.loads(raw_perms)
        permissions_objs = [Permission(perm["name"], perm["value"]) for perm in perms]
        return permissions_objs

    @st.dialog("Connection", width="large")
    def login():
        """Dialogue de connexion"""

        with st.form(key="login"):
            name = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")

            if st.form_submit_button("Se connecter"):
                search = find_user(name, password)  # On vérifie que l'utilisateur existe
                if search[0] is True:  # Si oui, alors c'est un succès
                    st.session_state["user"] = User(search[1][0], search[1][1], deserialize_perms(search[1][2]))
                    st.toast("Succès, redirection...", icon="✅")
                    st.balloons()
                    time.sleep(2)  # On attends 2 secondes avant de rediriger (pour les ballons)
                    st.rerun()
                elif search[1] == "Nom d'utilisateur incorrect":  # Si le nom d'utilisateur n'existe pas, on le communique à l'utilisateur
                    st.error("Nom d'utilisateur incorrect")
                elif search[1] == "Mot de passe incorrect":  # De même pour un mot de passe incorrect
                    st.error("Mot de passe incorrect")

    @st.dialog("Inscription", width="large")
    def register():
        """
        Dialogue d'inscription
        """

        def create_user(name, password, perms: Iterable[Permission]):
            """
            Écriture du nouvel utilisateur
            """
            # Si la raison de l'échec de find_user n'est pas nom d'utilisateur incorrect (soit mot de passe incorrect soit mot de passe bon), alors l'utilisateur existe. On affiche un toast
            if find_user(name, password)[1] != "Nom d'utilisateur incorrect":
                st.toast("Nom d'utilisateur deja pris", icon="❌")
            else:  # Sinon, on crée l'utilisateur et initialise les variables de session
                db.write([name, password, serialize_perms(perms)])
                st.session_state["user"] = User(name, password, perms)
                st.toast("Succès, redirection...", icon="✅")
                st.balloons()
                time.sleep(2)  # On attends 2 secondes avant de rediriger (pour les ballons)
                st.rerun()

        with st.form(key="sign in"):
            name = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("S'inscrire"):
                create_user(name, password, BASE_PERMS)  # On crée un utilisateur avec les permissions de base


def login_page():
    """Page de gestion du compte"""
    st.title("Connection")
    # Si l'utilisateur n'est pas connecté, on lui propose de se connecter
    if st.session_state["user"] is None:
        have_an_account = st.segmented_control("Avez-vous un compte ?", ["Oui", "Non"], key="have_an_account")
        if have_an_account == "Oui":
            login()
        elif have_an_account == "Non":
            register()
    else:  # Si l'utilisateur est connecté, on affiche son nom et on affiche les boutons de changement de mot de passe et de déconnexion
        st.info(f"Vous êtes connecté en tant que {st.session_state['user'].name}")
        change_password, disconnect = st.columns(2)
        change_password.button("Changer le mot de passe", on_click=change_password_dialog)
        disconnect.button("Déconnexion", on_click=logout_dialog)
