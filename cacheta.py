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
        acao = st.session_state.acoes.get(nome, "desistiu")

        st.session_state.stats[nome]["turnos"] += 1

        if acao == "venceu":
            st.session_state.stats[nome]["vitorias"] += 1

        elif acao == "perdeu":
            st.session_state.stats[nome]["derrotas"] += 1
            j["pontos"] -= 2

        else:
            st.session_state.stats[nome]["desistencias"] += 1
            j["pontos"] -= 1

        if j["pontos"] < 0:
            j["pontos"] = 0

        linha[nome] = j["pontos"]

    st.session_state.historico_turnos.append(linha)

    vivos = [j for j in st.session_state.jogadores if j["pontos"] > 0]
    mortos = [j for j in st.session_state.jogadores if j["pontos"] == 0]

    if vivos and len(mortos) == len(st.session_state.jogadores) - len(vivos):
        for v in vivos:
            st.session_state.stats[v["nome"]]["titulos"] += 1
        st.success("🏆 Jogo encerrado! Vencedores: " + ", ".join(v["nome"] for v in vivos))

    st.session_state.turno += 1
    st.session_state.acoes = {}

def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10

    st.session_state.turno = 1
    st.session_state.historico_turnos = []
    st.session_state.acoes = {}

# =====================
# INTERFACE
# =====================

aba_jogo, aba_stats = st.tabs(["🎮 Jogo", "📊 Estatísticas Gerais"])

# ======================================================
# ABA JOGO
# ======================================================

with aba_jogo:

    st.title("CACHETA")

    nome = st.text_input("Adicionar jogador")

    if st.button("Adicionar"):
        if nome:
            adicionar(nome)

    st.session_state.jogadores = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])

    st.subheader(f"Turno {st.session_state.turno}")

    for j in st.session_state.jogadores:

        acao = st.session_state.acoes.get(j["nome"], "")

        c1,c2,c3,c4,c5 = st.columns([3,1,2,2,1])

        c1.write(f"**{j['nome']}** — {j['pontos']} pts")

        j["ordem"] = c2.number_input(
            "Ordem",
            value=j["ordem"],
            key=j["nome"]+"_ordem",
            label_visibility="collapsed"
        )

        # ===== VENCEU =====
        with c3:
            cor = "#2ecc71" if acao == "venceu" else "#444"
            st.markdown(f"""
            <style>
            div[data-testid="stButton"][id="v_{j['nome']}"] button {{
                background:{cor};
                color:black;
            }}
            </style>
            """, unsafe_allow_html=True)

            if st.button("Venceu", key=f"v_{j['nome']}"):
                st.session_state.acoes[j["nome"]] = "venceu"

        # ===== PERDEU =====
        with c4:
            cor = "#e74c3c" if acao == "perdeu" else "#444"
            st.markdown(f"""
            <style>
            div[data-testid="stButton"][id="p_{j['nome']}"] button {{
                background:{cor};
                color:white;
            }}
            </style>
            """, unsafe_allow_html=True)

            if st.button("Perdeu", key=f"p_{j['nome']}"):
                st.session_state.acoes[j["nome"]] = "perdeu"

        # ===== EXCLUIR =====
        if c5.button("🗑", key=j["nome"]+"x"):
            excluir(j["nome"])
            st.experimental_rerun()

    st.divider()

    colA,colB,colC = st.columns(3)

    with colA:
        if st.button("Finalizar Turno"):
            finalizar_turno()

    with colB:
        if st.button("Reiniciar Turno"):
            reiniciar_turno()

    with colC:
        if st.button("Novo Jogo"):
            novo_jogo()

    # ===== TABELA =====
    if st.session_state.historico_turnos:

        df = pd.DataFrame(st.session_state.historico_turnos).set_index("Turno")
        st.subheader("Placar por Turno")
        st.dataframe(df, use_container_width=True)

        # ===== GRÁFICO =====
        df_m = df.reset_index().melt(id_vars="Turno", var_name="Jogador", value_name="Pontos")

        fig = px.line(df_m, x="Turno", y="Pontos", color="Jogador", markers=True)
        st.subheader("Gráfico de Desempenho")
        st.plotly_chart(fig, use_container_width=True)

# ======================================================
# ABA ESTATÍSTICAS
# ======================================================

with aba_stats:

    st.title("Estatísticas Gerais")

    dados = []

    for nome, s in st.session_state.stats.items():

        t = max(s["turnos"],1)

        dados.append({
            "Jogador": nome,
            "Turnos": s["turnos"],
            "% Vitórias": round(s["vitorias"]/t*100,1),
            "% Derrotas": round(s["derrotas"]/t*100,1),
            "% Desistências": round(s["desistencias"]/t*100,1),
            "Títulos": s["titulos"]
        })

    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)
