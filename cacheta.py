import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CACHETA", layout="wide")

# =====================
# ESTADO GLOBAL
# =====================

if "jogadores" not in st.session_state:
    st.session_state.jogadores = []

if "turno" not in st.session_state:
    st.session_state.turno = 1

if "acoes" not in st.session_state:
    st.session_state.acoes = {}

if "historico_turnos" not in st.session_state:
    st.session_state.historico_turnos = []

if "stats" not in st.session_state:
    st.session_state.stats = {}

# =====================
# FUNÇÕES
# =====================

def adicionar(nome):
    ordem = len(st.session_state.jogadores) + 1
    st.session_state.jogadores.append({
        "nome": nome,
        "pontos": 10,
        "ordem": ordem
    })

    if nome not in st.session_state.stats:
        st.session_state.stats[nome] = {
            "turnos": 0,
            "vitorias": 0,
            "derrotas": 0,
            "desistencias": 0,
            "titulos": 0
        }

def excluir(nome):
    st.session_state.jogadores = [j for j in st.session_state.jogadores if j["nome"] != nome]

def reiniciar_turno():
    st.session_state.acoes = {}

def finalizar_turno():

    linha = {"Turno": st.session_state.turno}

    for j in st.session_state.jogadores:

        nome = j["nome"]
        acao = st.session_state.acoes.get(nome, "desisti_
