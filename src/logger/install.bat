@echo on

REM Nom du projet (modifie ici si tu veux)
set PROJECT_NAME=frontend
REM Create folder if not exist
if not exist "frontend" mkdir frontend

REM Créer le projet avec Vite, framework Vanilla + JavaScript (pas d'interaction)
call npm create vite@latest %PROJECT_NAME% -- --template react --yes

if not exist "%PROJECT_NAME%\src" mkdir "%PROJECT_NAME%\src"

copy /y resources\main.js "%PROJECT_NAME%\main.js"
copy /y resources\index.html "%PROJECT_NAME%\index.html"
copy /y resources\vite.config.js "%PROJECT_NAME%\vite.config.js"
copy /y resources\src\App.jsx "%PROJECT_NAME%\src\App.jsx"

REM Aller dans le dossier
cd %PROJECT_NAME%

REM Installer les dépendances
npm install

REM Lancer le serveur de dev
npm run dev

pause