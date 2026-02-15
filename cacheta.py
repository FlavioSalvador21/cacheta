import streamlit as st
import pandas as pd
import plotly.express as px
import json, os

st.set_page_config(page_title="CACHETA", layout="wide")

ARQ = "cacheta_state.json"

# =====================================================
# Persistência
# =====================================================

def salvar():
    with open(ARQ, "w") as f:
        json.dump({
            "jogadores": st.session_state.jogadores,
            "turno": st.session_state.turno,
            "historico": st.session_state.historico,
            "acoes": st.session_state.historico_acoes
        }, f)

def carregar():
    if os.path.exists(ARQ):
        with open(ARQ) as f:
            d = json.load(f)
            st.session_state.jogadores = d.get("jogadores", [])
            st.session_state.turno = d.get("turno", 1)
            st.session_state.historico = d.get("historico", [])
            st.session_state.historico_acoes = d.get("acoes", [])

# =====================================================
# Estado inicial
# =====================================================

if "init" not in st.session_state:
    st.session_state.init = True
    st.session_state.jogadores = []
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    carregar()

# =====================================================
# Funções
# =====================================================

def adicionar():
    nome = st.session_state.novo_nome
    if not nome:
        return
    st.session_state.jogadores.append({"nome": nome, "pontos": 10, "ordem": len(st.session_state.jogadores)+1})
    st.session_state.novo_nome = ""
    salvar()

def excluir(nome):
    st.session_state.jogadores = [j for j in st.session_state.jogadores if j["nome"] != nome]
    salvar()

def finalizar_turno():

    selecoes = {}
    vencedores = []

    for j in st.session_state.jogadores:
        k = f"sel_{j['nome']}"
        acao = st.session_state.get(k)
        if acao == "Venceu":
            vencedores.append(j["nome"])
        selecoes[j["nome"]] = acao

    if len(vencedores) != 1:
        st.warning("Selecione exatamente 1 vencedor.")
        return

    linha = {"Turno": st.session_state.turno}
    linha_acoes = {}

    for j in st.session_state.jogadores:
        nome = j["nome"]
        acao = selecoes[nome] or "Desistiu"

        if acao == "Perdeu":
            j["pontos"] -= 2
        elif acao == "Desistiu":
            j["pontos"] -= 1

        j["pontos"] = max(j["pontos"], 0)

        linha[nome] = j["pontos"]
        linha_acoes[nome] = acao

        st.session_state[f"sel_{nome}"] = None  # reset selectbox

    st.session_state.historico.append(linha)
    st.session_state.historico_acoes.append(linha_acoes)
    st.session_state.turno += 1
    salvar()

def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    salvar()

# =====================================================
# UI
# =====================================================

st.title("CACHETA")

st.text_input("Adicionar jogador", key="novo_nome")
st.button("Adicionar", on_click=adicionar)

# Cabeçalho tipo tabela
h1,h2,h3,h4 = st.columns([3,1,3,1])
h1.markdown("**Jogador**")
h2.markdown("**Ordem**")
h3.markdown("**Resultado do turno**")
h4.markdown("**Excluir**")

st.session_state.jogadores = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])

for j in st.session_state.jogadores:

    c1,c2,c3,c4 = st.columns([3,1,3,1])

    c1.write(j["nome"])

    j["ordem"] = c2.number_input("", value=j["ordem"], key=f"ord_{j['nome']}", label_visibility="collapsed")

    c3.selectbox("", [None, "Venceu", "Perdeu"], key=f"sel_{j['nome']}")

    if c4.button("🗑", key=f"x_{j['nome']}"):
        excluir(j["nome"])
        st.experimental_rerun()

b1,b2 = st.columns(2)
b1.button("Finalizar Turno", on_click=finalizar_turno)
b2.button("Novo Jogo", on_click=novo_jogo)

# =====================================================
# Placar colorido + gráfico
# =====================================================

if st.session_state.historico:

    df = pd.DataFrame(st.session_state.historico).set_index("Turno")
    ac = pd.DataFrame(st.session_state.historico_acoes)

    sty = df.style

    for i in range(len(df)):
        for col in df.columns:
            cor = "#f1c40f"
            if ac.iloc[i][col] == "Venceu": cor = "#2ecc71"
            if ac.iloc[i][col] == "Perdeu": cor = "#e74c3c"

            sty = sty.set_properties(
                subset=pd.IndexSlice[[df.index[i]],[col]],
                **{"background-color": cor, "color": "black", "font-weight": "bold"}
            )

    st.subheader("Placar por turno")
    st.dataframe(sty, use_container_width=True)

    dm = df.reset_index().melt(id_vars="Turno", var_name="Jogador", value_name="Pontos")
    fig = px.line(dm, x="Turno", y="Pontos", color="Jogador", markers=True)
    st.plotly_chart(fig, use_container_width=True)
