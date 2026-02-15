import streamlit as st

st.set_page_config(page_title="CACHETA", layout="centered")

# =====================
# Inicialização
# =====================

if "jogadores" not in st.session_state:
    st.session_state.jogadores = []

if "turno" not in st.session_state:
    st.session_state.turno = 1

if "acoes" not in st.session_state:
    st.session_state.acoes = {}

if "historico" not in st.session_state:
    st.session_state.historico = []


# =====================
# Funções
# =====================

def adicionar(nome):
    st.session_state.jogadores.append({
        "nome": nome,
        "pontos": 10
    })

def marcar(nome, acao):
    st.session_state.acoes[nome] = acao

def finalizar_turno():

    resumo = {"turno": st.session_state.turno, "resultados": []}

    for j in st.session_state.jogadores:

        nome = j["nome"]

        # quem não foi marcado -> desistiu
        acao = st.session_state.acoes.get(nome, "desistiu")

        if acao == "perdeu":
            j["pontos"] -= 2
        elif acao == "desistiu":
            j["pontos"] -= 1

        resumo["resultados"].append({
            "nome": nome,
            "acao": acao,
            "pontos": j["pontos"]
        })

    st.session_state.historico.append(resumo)
    st.session_state.turno += 1
    st.session_state.acoes = {}


def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10

    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.acoes = {}


# =====================
# Interface
# =====================

st.title("CACHETA")

nome = st.text_input("Adicionar jogador")

if st.button("Adicionar"):
    if nome:
        adicionar(nome)

st.divider()

st.subheader(f"Turno {st.session_state.turno}")

# Jogadores + botões
for j in st.session_state.jogadores:

    col1, col2, col3, col4 = st.columns([3,2,2,2])

    col1.write(f"**{j['nome']}** — {j['pontos']} pts")

    if col2.button("Venceu", key=j["nome"]+"v"):
        marcar(j["nome"], "venceu")

    if col3.button("Perdeu", key=j["nome"]+"p"):
        marcar(j["nome"], "perdeu")

    if col4.button("Desistiu", key=j["nome"]+"d"):
        marcar(j["nome"], "desistiu")


st.divider()

if st.button("Finalizar Turno"):
    finalizar_turno()

if st.button("Novo Jogo"):
    novo_jogo()

# =====================
# Histórico
# =====================

st.divider()
st.subheader("Histórico de Turnos")

for t in st.session_state.historico:

    st.markdown(f"### Turno {t['turno']}")

    for r in t["resultados"]:
        st.write(f"{r['nome']} — {r['acao']} → {r['pontos']} pts")


