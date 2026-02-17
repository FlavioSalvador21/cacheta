import streamlit as st
import pandas as pd
import plotly.express as px
import json, os

st.set_page_config(page_title="CACHETA - FLÁVIO", layout="wide")

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
        try:
            with open(ARQ) as f:
                d = json.load(f)
                st.session_state.jogadores = d.get("jogadores", [])
                st.session_state.turno = d.get("turno", 1)
                st.session_state.historico = d.get("historico", [])
                st.session_state.historico_acoes = d.get("acoes", [])
        except:
            pass

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
# Funções de Ação
# =====================================================

def adicionar():
    nome = st.session_state.novo_nome
    if not nome:
        return
    st.session_state.jogadores.append({
        "nome": nome,
        "pontos": 10,
        "ordem": len(st.session_state.jogadores) + 1,
        "pago": False  # Inicia como não pago
    })
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

    st.session_state.historico.append(linha)
    st.session_state.historico_acoes.append(linha_acoes)
    st.session_state.turno += 1
    salvar()

def novo_jogo():
    for j in st.session_state.jogadores:
        j["pontos"] = 10
        j["pago"] = False  # RESETA O PAGAMENTO APENAS AQUI
    st.session_state.turno = 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    salvar()

# =====================================================
# UI - Interface do Usuário
# =====================================================

st.title("🃏 CACHETA MANAGER")

with st.expander("➕ Adicionar Jogador"):
    col_add1, col_add2 = st.columns([3, 1])
    col_add1.text_input("Nome do jogador", key="novo_nome", label_visibility="collapsed")
    col_add2.button("Adicionar", on_click=adicionar, use_container_width=True)

# Cabeçalho da Tabela de Controle
st.markdown("---")
h1, h2, h3, h4, h5 = st.columns([2, 1, 2, 1, 1])
h1.markdown("**Jogador**")
h2.markdown("**Ordem**")
h3.markdown("**Ação do Turno**")
h4.markdown("**Pago?**")
h5.markdown("**Excluir**")

# Ordenação dos jogadores
st.session_state.jogadores = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])

for j in st.session_state.jogadores:
    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
    
    c1.write(f"**{j['nome']}**")

    # Controle de Ordem
    nova_ordem = c2.number_input("", value=j["ordem"], key=f"ord_{j['nome']}", label_visibility="collapsed")
    if nova_ordem != j["ordem"]:
        j["ordem"] = nova_ordem
        salvar()

    # Seleção de resultado
    c3.selectbox("", [None, "Venceu", "Perdeu", "Desistiu"], key=f"sel_{j['nome']}", label_visibility="collapsed")

    # Controle de Pagamento (Persistente)
    pago_db = j.get("pago", False)
    check_pago = c4.checkbox("Sim", value=pago_db, key=f"pago_chk_{j['nome']}")
    if check_pago != pago_db:
        j["pago"] = check_pago
        salvar()

    # Excluir
    if c5.button("🗑", key=f"del_{j['nome']}"):
        excluir(j["nome"])
        st.rerun()

st.markdown("---")
b1, b2 = st.columns(2)
b1.button("✅ Finalizar Turno", on_click=finalizar_turno, use_container_width=True)
b2.button("🔄 Novo Jogo / Resetar Tudo", on_click=novo_jogo, use_container_width=True)

# =====================================================
# Placar e Gráficos
# =====================================================

if st.session_state.historico:
    st.subheader("📊 Placar Geral por Turno")
    
    df = pd.DataFrame(st.session_state.historico).set_index("Turno")
    ac = pd.DataFrame(st.session_state.historico_acoes)

    # Estilização da Tabela
    def style_placar(styler):
        for i in range(len(df)):
            for col in df.columns:
                acao = ac.iloc[i][col]
                cor = "#f1c40f"  # Amarelo (Desistiu)
                texto = "black"
                if acao == "Venceu":
                    cor = "#2ecc71"; texto = "white"
                elif acao == "Perdeu":
                    cor = "#e74c3c"; texto = "white"
                
                styler.set_properties(
                    subset=pd.IndexSlice[[df.index[i]], [col]],
                    **{
                        "background-color": cor,
                        "color": texto,
                        "font-weight": "bold",
                        "text-align": "center"
                    }
                )
        return styler

    # Aplicar estilos e centralizar cabeçalhos
    sty = df.style.pipe(style_placar).set_table_styles(
        [{"selector": "th", "props": [("text-align", "center"), ("background-color", "#f8f9fa")]}]
    )

    st.table(sty)

    # Gráfico de Evolução
    st.subheader("📈 Evolução das Pontuações")
    dm = df.reset_index().melt(id_vars="Turno", var_name="Jogador", value_name="Pontos")
    fig = px.line(dm, x="Turno", y="Pontos", color="Jogador", markers=True, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Inicie a partida para visualizar o histórico de pontos.")
