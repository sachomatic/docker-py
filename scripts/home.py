import streamlit as st

def home():
    st.title("Page d'accueil")

    st.write("Ce site web désigné par mes soins vous permets de contrôler le serveur Minecraft à distance.")
    st.write("Le site est un peu expérimental, donc vous attendez pas à des miracles.")
    st.divider()

    st.header("Lancement du serveur")
    st.write("Pour lancer le serveur, aller sur la page Conteneurs, puis cliquer sur Lancer le compose")
    st.page_link(st.session_state["pages"][1],label="Aller sur la page Conteneurs",icon="↗")
    st.divider()
    
    st.header("Devlog")
    st.write("Putain comment c'était un enfer ce site, vous imaginez même pas. D'abord, faut parler du fait que les 3/4 du temps où j'ai bossé, c'était sur les putain de logs, alors que personne va les utiliser!")
    st.write("Ah et ces putains de cookies, ya jamais rien qui marche. Bref vous avez intêret à aimer ce site.")