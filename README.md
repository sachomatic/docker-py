# Docker-Py

Docker-Py est un projet visant à créer une interface web pour gérer des conteneurs Docker. Il est majoritairement pour permettre aux gens de lancer et d'éteindre mon serveur minecraft quand je ne suis pas là.
Il permet de lancer et d'arrêter des conteneurs, de consulter les logs, de gérer les utilisateurs et leurs permissions.

## Fonctionnalités

* Gestion des conteneurs Docker (lancement, arrêt, consultation des logs)
* Gestion des utilisateurs et de leurs permissions
* Interface web simple et intuitive

## Installation

Pour installer Docker-Py, vous pouvez suivre les étapes suivantes :

1. Clonez le repository Git
2. Installez les dépendances avec `pip install -r requirements.txt`
3. Copiez le modpack (Ce doit être un modpack serveur par contre). Le nom de base est server_pack.zip en forge-1.20.1-47.3.0 mais vous pouvez le modifiez (voir ci-dessous)
4. Exécutez le script `install.bat` pour installer le serveur Vite
5. Exécutez le script `run.py` pour lancer l'application!

## Utilisation

Une fois l'application lancée, vous pouvez créer un compte et vous connectez. En tant qu'admin vous pourrez ensuite vous donnez des permissions.
Vous pouvez ensuite gérer les conteneurs et les utilisateurs en utilisant les boutons et les formulaire de l'interface web.

## Configuration

Vous pouvez configurer l'application en modifiant les fichiers de configuration (`config.ini` et `docker-compose.yml`).
Vous pouvez également modifier le code source pour personnaliser l'application à vos besoins
