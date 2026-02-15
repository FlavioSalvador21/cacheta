import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CACHETA", layout="wide")

# =====================
# ESTADO
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
    st.session_state.acoes.pop(nome, None)

def reiniciar_turno():
    st.session_state.acoes = {}

def selecionar_acao(nome, acao):
    # garante vencedor único
    if acao == "Venceu":
        for k in list(st.session_state.acoes.keys()):
            if st.session_state.acoes.get(k) == "Venceu":
                st.session_state.acoes[k] = ""
    st.session_state.acoes[nome] = acao

def finalizar_turno():

    vencedores = [k for k,v in st.session_state.acoes.items() if v=="Venceu"]
    if len(vencedores) != 1:
        st.warning("Selecione exatamente 1 vencedor.")
        return

    linha = {"Turno": st.session_state.turno}

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

        # salva pontos + ação (ex: "8|Perdeu")
        linha[nome] = f"{j['pontos']}|{acao}"

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

        c1,c2,c3,c4 = st.columns([3,1,4,1])

        c1.write(f"**{j['nome']}** — {j['pontos']} pts")

        j["ordem"] = c2.number_input(
            "Ordem",
            value=j["ordem"],
            key=j["nome"]+"_ordem",
            label_visibility="collapsed"
        )

        escolha = c3.radio(
            "",
            ["","Venceu","Perdeu"],
            horizontal=True,
            key=f"acao_{j['nome']}"
        )

        if escolha:
            selecionar_acao(j["nome"], escolha)

        if c4.button("🗑", key=j["nome"]+"x"):
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

    # ===== TABELA COLORIDA =====
    if st.session_state.historico_turnos:

        df = pd.DataFrame(st.session_state.historico_turnos).set_index("Turno")

        def estilo(valor):
            if isinstance(valor,str) and "|" in valor:
                pts, acao = valor.split("|")
                if acao == "Venceu":
                    return "background-color:#2ecc71;color:black"
                if acao == "Perdeu":
                    return "background-color:#e74c3c;color:white"
                if acao == "Desistiu":
                    return "background-color:#f1c40f;color:black"
            return ""

        styled = df.style.applymap(estilo)

        st.subheader("Placar por Turno (colorido)")
        st.dataframe(styled, use_container_width=True)

        # ===== GRÁFICO =====
        # remove ação, fica só pontos
        df_pts = df.applymap(lambda x: int(x.split("|")[0]))
        df_m = df_pts.reset_index().melt(id_vars="Turno", var_name="Jogador", value_name="Pontos")

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
