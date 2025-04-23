import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import dotenv,os

from scripts.login import User,serialize_perms,deserialize_perms
dotenv.load_dotenv()

token = os.getenv("TOKEN")

class Cookies():
    def __init__(self):
        # Création du cookie manager avec une clé secrète pour le chiffrement
        self.cookies = EncryptedCookieManager(
            prefix="myapp_",  # préfixe pour éviter les conflits de cookies
            password=token
        )

        if not self.cookies.ready():
            # On attend que le gestionnaire de cookies soit prêt (on arrête l'éxecution de la page en attendant)
            st.stop()

    def read_cookies(self):
        # Lecture du cookie user_id et password
        username = self.cookies.get("user_id")
        password = self.cookies.get("password")
        # Si aucun cookie n'est trouvé, on renvoie None
        if username == None or username == "none":
            return None
        # Sinon, on crée un User et on le retourne avec les permissions trouvées
        else:
            permissions = self.cookies.get("permissions")
            permissions = deserialize_perms(permissions)
            return User(username,password,permissions)

    def write_cookies(self, user:User):
        # On écrit le nom d'utilisateur, le mot de passe et les permissions (serialisées) dans les cookies
        self.cookies["user_id"] = user.name
        self.cookies["password"] = user.password
        self.cookies["permissions"] = serialize_perms(user.permissions)
        self.cookies.save()
    
    def clear_cookies(self):
        # On mets tous les cookies à "none" faute de pouvoir les mettre à None, ce qui renvoie une erreur.
        self.cookies["user_id"] = "none"
        self.cookies["password"] = "none"
        self.cookies["permissions"] = "none"
        self.cookies.save()
