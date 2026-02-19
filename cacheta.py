import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="CACHETA MANAGER - FLÁVIO", layout="wide")

# =====================================================
# ESTADO INICIAL (Memória temporária do navegador)
# =====================================================
if "jogadores" not in st.session_state:
    st.session_state.jogadores = []
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []

# =====================================================
# FUNÇÕES DE LÓGICA
# =====================================================
def adicionar():
    nome = st.session_state.novo_nome
    if nome:
        st.session_state.jogadores.append({
            "nome": nome, "pontos": 10, "ordem": len(st.session_state.jogadores) + 1, "pago": False
        })
        st.session_state.novo_nome = ""

def finalizar_turno():
    vencedores = [j["nome"] for j in st.session_state.jogadores if st.session_state.get(f"sel_{j['nome']}") == "Venceu"]
    if len(vencedores) != 1:
        st.warning("Selecione exatamente 1 vencedor.")
        return

    linha_pontos = {"Turno": st.session_state.turno}
    linha_acoes = {}

    for j in st.session_state.jogadores:
        nome = j["nome"]
        key_sel = f"sel_{nome}"
        acao = st.session_state.get(key_sel) or "Desistiu"
        
        if acao == "Perdeu": j["pontos"] -= 2
        elif acao == "Desistiu": j["pontos"] -= 1
        j["pontos"] = max(j["pontos"], 0)
        
        linha_pontos[nome] = j["pontos"]
        linha_acoes[nome] = acao
        st.session_state[key_sel] = None # Volta para "vazio" o seletor

    st.session_state.historico.append(linha_pontos)
    st.session_state.historico_acoes.append(linha_acoes)
    st.session_state.turno += 1

def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10
        j["pago"] = False # O pagamento só reseta aqui
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []

# =====================================================
# INTERFACE (UI) E CSS
# =====================================================
st.title("🃏 CACHETA MANAGER")

# CSS para centralização total e cabeçalhos brancos
st.markdown("""
    <style>
    .stTable td, .stTable th {
        text-align: center !important;
        vertical-align: middle !important;
        height: 60px !important;
    }
    .stTable th {
        color: white !important;
        background-color: #0E1117 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

with st.expander("👤 Gerenciar Jogadores"):
    c1, c2 = st.columns([3, 1])
    c1.text_input("Nome", key="novo_nome", label_visibility="collapsed")
    c2.button("Adicionar", on_click=adicionar, use_container_width=True)

st.markdown("---")
h = st.columns([2, 1, 2, 1, 1])
for col, tit in zip(h, ["Jogador", "Ordem", "Resultado", "Pago?", "Ação"]):
    col.write(f"**{tit}**")

st.session_state.jogadores = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])

for j in st.session_state.jogadores:
    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
    c1.write(f"**{j['nome']}**")
    j["ordem"] = c2.number_input("", value=j["ordem"], key=f"ord_{j['nome']}", label_visibility="collapsed")
    c3.selectbox("", [None, "Venceu", "Perdeu", "Desistiu"], key=f"sel_{j['nome']}", label_visibility="collapsed")
    j["pago"] = c4.checkbox("Sim", value=j["pago"], key=f"pago_{j['nome']}")
    if c5.button("🗑", key=f"del_{j['nome']}"):
        st.session_state.jogadores = [jog para jog in st.session_state.jogadores if jog["nome"] != j["nome"]]
        st.rerun()

st.markdown("---")
b1, b2 = st.columns(2)
b1.button("✅ Finalizar Turno", on_click=finalizar_turno, use_container_width=True)
b2.button("🔄 Novo Jogo", on_click=novo_jogo, use_container_width=True)

# =====================================================
# PLACAR VISUAL
# =====================================================
if st.session_state.historico:
    st.subheader("📊 Placar da Partida")
    df = pd.DataFrame(st.session_state.historico).set_index("Turno")
    ac = pd.DataFrame(st.session_state.historico_acoes)

    def style_placar(styler):
        for i in range(len(df)):
            max_v = df.iloc[i].max()
            for col in df.columns:
                acao = ac.iloc[i][col]
                pts = df.iloc[i][col]
                bg = "#f1c40f"; tx = "black"
                if acao == "Venceu": bg = "#2ecc71"; tx = "white"
                elif acao == "Perdeu": bg = "#e74c3c"; tx = "white"
                
                est = {"background-color": bg, "color": tx, "font-weight": "bold"}
                if pts == max_v and max_v > 0:
                    est["border"] = "4px solid #00ff00"; est["border-radius"] = "10px"
                if pts in [1, 2]:
                    est["color"] = "#FF0000"; est["font-size"] = "1.3em" # Vermelho forte
                styler.set_properties(subset=pd.IndexSlice[[df.index[i]], [col]], **est)
        return styler

    st.table(df.astype(str).replace(["0", "0.0"], "X").style.pipe(style_placar))
    st.plotly_chart(px.line(df.reset_index().melt(id_vars="Turno"), x="Turno", y="value", color="variable", markers=True), use_container_width=True)
