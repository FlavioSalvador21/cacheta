import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="CACHETA", layout="wide")

ARQ = "cacheta_state.json"

# =================================================
# PERSISTÊNCIA
# =================================================

def salvar_estado():
    data = {
        "jogadores": st.session_state.jogadores,
        "turno": st.session_state.turno,
        "historico_turnos": st.session_state.historico_turnos,
        "historico_acoes": st.session_state.historico_acoes,
        "stats": st.session_state.stats
    }
    with open(ARQ, "w") as f:
        json.dump(data, f)

def carregar_estado():
    if os.path.exists(ARQ):
        with open(ARQ) as f:
            data = json.load(f)
            st.session_state.jogadores = data.get("jogadores", [])
            st.session_state.turno = data.get("turno", 1)
            st.session_state.historico_turnos = data.get("historico_turnos", [])
            st.session_state.historico_acoes = data.get("historico_acoes", [])
            st.session_state.stats = data.get("stats", {})

# =================================================
# ESTADO INICIAL
# =================================================

if "init" not in st.session_state:
    st.session_state.init = True
    st.session_state.jogadores = []
    st.session_state.turno = 1
    st.session_state.acoes = {}
    st.session_state.historico_turnos = []
    st.session_state.historico_acoes = []
    st.session_state.stats = {}
    carregar_estado()

# =================================================
# FUNÇÕES
# =================================================

def adicionar():
    nome = st.session_state.novo_nome
    if not nome:
        return

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

    st.session_state.novo_nome = ""
    salvar_estado()

def excluir(nome):
    st.session_state.jogadores = [j for j in st.session_state.jogadores if j["nome"] != nome]
    salvar_estado()

def reiniciar_turno():
    st.session_state.acoes = {}

def selecionar_acao(nome, acao):

    # garante apenas 1 vencedor
    if acao == "Venceu":
        for k in list(st.session_state.acoes.keys()):
            if st.session_state.acoes.get(k) == "Venceu":
                st.session_state.acoes[k] = ""

    st.session_state.acoes[nome] = acao

def finalizar_turno():

    vencedores = [k for k,v in st.session_state.acoes.items() if v == "Venceu"]
    if len(vencedores) != 1:
        st.warning("Selecione exatamente 1 vencedor.")
        return

    linha_p = {"Turno": st.session_state.turno}
    linha_a = {}

    for j in st.session_state.jogadores:

        nome = j["nome"]
        acao = st.session_state.acoes.get(nome, "Desistiu")

        st.session_state.stats[nome]["turnos"] += 1

        if acao == "Venceu":
            st.session_state.stats[nome]["vitorias"] += 1
        elif acao == "Perdeu":
            st.session_state.stats[nome]["derrotas"] += 1
            j["pontos"] -= 2
        else:
            st.session_state.stats[nome]["desistencias"] += 1
            j["pontos"] -= 1

        if j["pontos"] < 0:
            j["pontos"] = 0

        linha_p[nome] = j["pontos"]
        linha_a[nome] = acao

    st.session_state.historico_turnos.append(linha_p)
    st.session_state.historico_acoes.append(linha_a)

    reiniciar_turno()
    st.session_state.turno += 1
    salvar_estado()

def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10

    st.session_state.turno = 1
    st.session_state.historico_turnos = []
    st.session_state.historico_acoes = []
    reiniciar_turno()
    salvar_estado()

# =================================================
# UI
# =================================================

aba_jogo, aba_stats = st.tabs(["🎮 Jogo", "📊 Estatísticas"])

with aba_jogo:

    st.title("CACHETA")

    st.text_input("Adicionar jogador", key="novo_nome")
    st.button("Adicionar", on_click=adicionar)

    st.session_state.jogadores = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])

    st.subheader(f"Turno {st.session_state.turno}")

    for j in st.session_state.jogadores:

        c1,c2,c3,c4 = st.columns([3,1,4,1])

        c1.write(f"**{j['nome']}** — {j['pontos']} pts")

        j["ordem"] = c2.number_input("", value=j["ordem"], key=j["nome"]+"_ordem", label_visibility="collapsed")

        escolha = c3.radio("", ["","Venceu","Perdeu"], horizontal=True, key=f"acao_{j['nome']}")
        if escolha:
            selecionar_acao(j["nome"], escolha)

        if c4.button("🗑", key=j["nome"]+"x"):
            excluir(j["nome"])
            st.experimental_rerun()

    colA,colB,colC = st.columns(3)
    if colA.button("Finalizar Turno"): finalizar_turno()
    if colB.button("Reiniciar Turno"): reiniciar_turno()
    if colC.button("Novo Jogo"): novo_jogo()

    if st.session_state.historico_turnos:

        df = pd.DataFrame(st.session_state.historico_turnos).set_index("Turno")
        df_ac = pd.DataFrame(st.session_state.historico_acoes)

        styled = df.style

        for i in range(len(df)):
            for col in df.columns:
                cor = "#f1c40f"
                if df_ac.iloc[i][col] == "Venceu": cor = "#2ecc71"
                if df_ac.iloc[i][col] == "Perdeu": cor = "#e74c3c"
                styled = styled.set_properties(subset=pd.IndexSlice[[df.index[i]],[col]], **{"background-color": cor})

        st.subheader("Placar por Turno")
        st.dataframe(styled, use_container_width=True)

        df_m = df.reset_index().melt(id_vars="Turno", var_name="Jogador", value_name="Pontos")
        fig = px.line(df_m, x="Turno", y="Pontos", color="Jogador", markers=True)
        st.plotly_chart(fig, use_container_width=True)

with aba_stats:

    dados = []
    for n,s in st.session_state.stats.items():
        t = max(s["turnos"],1)
        dados.append({
            "Jogador": n,
            "% Vitórias": round(s["vitorias"]/t*100,1),
            "% Derrotas": round(s["derrotas"]/t*100,1),
            "% Desistências": round(s["desistencias"]/t*100,1),
            "Turnos": s["turnos"]
        })

    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)
