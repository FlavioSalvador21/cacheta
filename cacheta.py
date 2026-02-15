import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CACHETA", layout="wide")

if "jogadores" not in st.session_state:
    st.session_state.jogadores = []

if "turno" not in st.session_state:
    st.session_state.turno = 1

if "historico" not in st.session_state:
    st.session_state.historico = []

if "stats" not in st.session_state:
    st.session_state.stats = {}

def adicionar(nome):
    st.session_state.jogadores.append({"nome": nome, "pontos": 10})

    if nome not in st.session_state.stats:
        st.session_state.stats[nome] = {"v":0,"p":0,"d":0,"t":0}

st.title("CACHETA")

nome = st.text_input("Jogador")
if st.button("Adicionar"):
    adicionar(nome)

for j in st.session_state.jogadores:

    st.write(f"### {j['nome']} — {j['pontos']} pts")

    acao = st.radio(
        "",
        ["Venceu","Perdeu","Desistiu"],
        horizontal=True,
        key=f"acao_{j['nome']}"
    )

    st.session_state.stats[j["nome"]]["t"] += 1

    if acao=="Venceu":
        st.session_state.stats[j["nome"]]["v"] += 1

    if acao=="Perdeu":
        j["pontos"] -= 2
        st.session_state.stats[j["nome"]]["p"] += 1

    if acao=="Desistiu":
        j["pontos"] -= 1
        st.session_state.stats[j["nome"]]["d"] += 1

if st.button("Finalizar Turno"):
    st.experimental_rerun()
