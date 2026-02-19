import streamlit as st
import pandas as pd
import plotly.express as px
import json, os

st.set_page_config(page_title="CACHETA MANAGER - FLÁVIO", layout="wide")

ARQ = "cacheta_state.json"

# =====================================================
# Persistência de Dados
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
        try:
            with open(ARQ) as f:
                d = json.load(f)
                st.session_state.jogadores = d.get("jogadores", [])
                st.session_state.turno = d.get("turno", 1)
                st.session_state.historico = d.get("historico", [])
                st.session_state.historico_acoes = d.get("acoes", [])
        except:
            pass

if "init" not in st.session_state:
    st.session_state.jogadores = []
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    carregar()
    st.session_state.init = True

# =====================================================
# Funções de Lógica
# =====================================================

def adicionar():
    nome = st.session_state.novo_nome
    if not nome: return
    st.session_state.jogadores.append({
        "nome": nome, "pontos": 10, "ordem": len(st.session_state.jogadores) + 1, "pago": False
    })
    st.session_state.novo_nome = ""
    salvar()

def excluir(nome):
    st.session_state.jogadores = [j for j in st.session_state.jogadores if j["nome"] != nome]
    salvar()

def finalizar_turno():
    vencedores = [j["nome"] for j in st.session_state.jogadores if st.session_state.get(f"sel_{j['nome']}") == "Venceu"]
    if len(vencedores) != 1:
        st.warning("Selecione exatamente 1 vencedor.")
        return

    linha = {"Turno": st.session_state.turno}
    linha_acoes = {}

    for j in st.session_state.jogadores:
        nome = j["nome"]
        acao = st.session_state.get(f"sel_{nome}") or "Desistiu"
        
        if acao == "Perdeu": j["pontos"] -= 2
        elif acao == "Desistiu": j["pontos"] -= 1

        j["pontos"] = max(j["pontos"], 0)
        linha[nome] = j["pontos"]
        linha_acoes[nome] = acao

    st.session_state.historico.append(linha)
    st.session_state.historico_acoes.append(linha_acoes)
    st.session_state.turno += 1
    salvar()

def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10
        j["pago"] = False 
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    salvar()

# =====================================================
# Interface (UI) e CSS Injetado
# =====================================================

st.title("🃏 CACHETA MANAGER")

# CSS para centralização absoluta e cabeçalhos brancos
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
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

with st.expander("➕ Gerenciar Jogadores"):
    c_a1, c_a2 = st.columns([3, 1])
    c_a1.text_input("Nome do novo jogador", key="novo_nome", label_visibility="collapsed")
    c_a2.button("Adicionar", on_click=adicionar, use_container_width=True)

st.markdown("---")
h1, h2, h3, h4, h5 = st.columns([2, 1, 2, 1, 1])
h1.write("**Jogador**"); h2.write("**Ordem**"); h3.write("**Ação Turno**"); h4.write("**Pago?**"); h5.write("**Excluir**")

st.session_state.jogadores = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])

for j in st.session_state.jogadores:
    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
    c1.write(f"**{j['nome']}**")
    j["ordem"] = c2.number_input("", value=j["ordem"], key=f"ord_{j['nome']}", label_visibility="collapsed")
    c3.selectbox("", [None, "Venceu", "Perdeu", "Desistiu"], key=f"sel_{j['nome']}", label_visibility="collapsed")
    
    pago_db = j.get("pago", False)
    if c4.checkbox("Pago", value=pago_db, key=f"pago_chk_{j['nome']}") != pago_db:
        j["pago"] = not pago_db
        salvar()
        
    if c5.button("🗑", key=f"del_{j['nome']}"):
        excluir(j["nome"])
        st.rerun()

st.markdown("---")
b1, b2 = st.columns(2)
b1.button("✅ Finalizar Turno", on_click=finalizar_turno, use_container_width=True)
b2.button("🔄 Novo Jogo / Resetar Pagamentos", on_click=novo_jogo, use_container_width=True)

# =====================================================
# Placar e Estilização Avançada
# =====================================================

if st.session_state.historico:
    st.subheader("📊 Placar Dinâmico")
    
    df = pd.DataFrame(st.session_state.historico).set_index("Turno")
    ac = pd.DataFrame(st.session_state.historico_acoes)
    df_display = df.astype(str).replace(["0", "0.0"], "X")

    def aplicar_estilos(styler):
        for i in range(len(df)):
            max_turno = df.iloc[i].max()
            for col in df.columns:
                pontos = df.iloc[i][col]
                acao = ac.iloc[i][col]
                
                # Cores base por ação
                bg = "#f1c40f"; tx = "black"
                if acao == "Venceu": bg = "#2ecc71"; tx = "white"
                elif acao == "Perdeu": bg = "#e74c3c"; tx = "white"
                
                estilos = {
                    "background-color": bg,
                    "color": tx,
                    "font-weight": "bold",
                    "text-align": "center",
                    "vertical-align": "middle"
                }

                # LÍDER DO TURNO: Borda verde
                if pontos == max_turno and pontos > 0:
                    estilos["border"] = "4px solid #00ff00"
                    estilos["border-radius"] = "12px"

                # ALERTA DE ROÇA: 1 ou 2 pontos em Vermelho Forte
                if pontos in [1, 2]:
                    estilos["color"] = "#FF0000"  # Vermelho Vivo
                    estilos["font-size"] = "1.3em"
                    estilos["text-shadow"] = "1px 1px 1px rgba(0,0,0,0.2)"

                # X DE ELIMINAÇÃO: Zerados
                if pontos == 0:
                    estilos["color"] = "black"
                    estilos["font-size"] = "1.5em"

                styler.set_properties(subset=pd.IndexSlice[[df.index[i]], [col]], **estilos)
        return styler

    sty = df_display.style.pipe(aplicar_estilos)
    st.table(sty)

    # Gráfico
    st.subheader("📈 Evolução da Partida")
    dm = df.reset_index().melt(id_vars="Turno", var_name="Jogador", value_name="Pontos")
    st.plotly_chart(px.line(dm, x="Turno", y="Pontos", color="Jogador", markers=True), use_container_width=True)

else:
    st.info("Aguardando o primeiro turno para gerar o placar.")
