from json import JSONDecodeError
from logging import getLogger
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import dotenv
import os

from scripts.corruptiontracker import CorruptionTracker
from scripts.login import BASE_PERMS, User, serialize_perms, deserialize_perms


logger = getLogger(__name__)

dotenv.load_dotenv()

env_token = os.getenv("TOKEN")
if env_token is None:
    logger.fatal("TOKEN is not set in the environment variables or .env file.")
    st.error("TOKEN is not set in the environment variables or .env file.")
    st.stop()
token: str = env_token


class Cookies:
    def __init__(self):
        # Création du cookie manager avec une clé secrète pour le chiffrement
        self.cookies = EncryptedCookieManager(
            prefix="myapp_",  # préfixe pour éviter les conflits de cookies
            password=token,
        )

        if not self.cookies.ready():
            # On attend que le gestionnaire de cookies soit prêt (on arrête l’exécution de la page en attendant)
            st.stop()

    def read_cookies(self):
        global CorruptionTracker
        # Lecture du cookie user_id et password
        username = self.cookies.get("user_id")
        if username is None or username == "none":  # L'utilisateur n'est pas connecté
            return
        password = self.cookies.get("password")
        if password is None:  # Le mot de passe est corrompu
            logger.warning(f"Utilisateur {username} n'a pas de mot de passe assigné dans ses cookies, ses cookies seront supprimés")
            # On supprime les cookies
            self.clear_cookies()
            return
        # Si les cookies sont trouvé, on crée un User et on le retourne avec les permissions trouvées
        perms_cookie = self.cookies.get("permissions")
        if perms_cookie is None:
            logger.warning(f"Utilisateur {username} n'a pas de permissions assignées dans ses cookies, ses permissions seront réinitialisées")
            CorruptionTracker += 1
            perms = BASE_PERMS
        else:
            try:
                perms = deserialize_perms(perms_cookie)
            except JSONDecodeError as deserialization_error:
                CorruptionTracker += 1
                print(deserialization_error)
                logger.error(f"Erreur de décodage des permissions pour l'utilisateur {username}, les permissions seront réinitialisées")
                perms = BASE_PERMS
        return User(username, password, perms)

    def write_cookies(self, user: User):
        # On écrit le nom d'utilisateur, le mot de passe et les permissions (sérialisées) dans les cookies
        print("Initialisation des cookies")
        self.cookies["user_id"] = user.name
        self.cookies["password"] = user.password
        self.cookies["permissions"] = serialize_perms(user.perms)
        self.cookies.save()

    def clear_cookies(self):
        # On mets tous les cookies à "none" faute de pouvoir les mettre à None (qui renvoie une erreur).
        print("Réinitialisation des cookies")
        self.cookies["user_id"] = "none"
        self.cookies["password"] = "none"
        self.cookies["permissions"] = "none"
        self.cookies.save()
