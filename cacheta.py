import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os

# Configuração da Página
st.set_page_config(page_title="CACHETA SQL - FLÁVIO", layout="wide")

DB_NAME = "cacheta_dados.db"

# =====================================================
# FUNÇÕES DE BANCO DE DADOS (SQLITE)
# =====================================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabela de Jogadores (Estado Atual)
    c.execute('''CREATE TABLE IF NOT EXISTS jogadores 
                 (nome TEXT PRIMARY KEY, pontos INTEGER, ordem INTEGER, pago BOOLEAN)''')
    # Tabela de Histórico (Registros de todos os turnos)
    c.execute('''CREATE TABLE IF NOT EXISTS historico 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, turno INTEGER, nome TEXT, pontos_resultantes INTEGER, acao TEXT)''')
    conn.commit()
    conn.close()

def salvar_jogador_db(nome, pontos, ordem, pago):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO jogadores VALUES (?, ?, ?, ?)", (nome, pontos, ordem, pago))
    conn.commit()
    conn.close()

def registrar_turno_db(turno, nome, pontos, acao):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO historico (turno, nome, pontos_resultantes, acao) VALUES (?, ?, ?, ?)", 
              (turno, nome, pontos, acao))
    conn.commit()
    conn.close()

def carregar_dados_db():
    conn = sqlite3.connect(DB_NAME)
    # Carregar Jogadores
    jogadores_df = pd.read_sql_query("SELECT * FROM jogadores", conn)
    # Carregar Histórico para reconstruir session_state se necessário
    historico_df = pd.read_sql_query("SELECT * FROM historico", conn)
    conn.close()
    return jogadores_df, historico_df

def limpar_banco_novo_jogo():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE jogadores SET pontos = 10, pago = 0")
    c.execute("DELETE FROM historico")
    conn.commit()
    conn.close()

# =====================================================
# ESTADO INICIAL
# =====================================================

init_db()

if "init" not in st.session_state:
    j_df, h_df = carregar_dados_db()
    st.session_state.jogadores = j_df.to_dict('records')
    st.session_state.turno = int(h_df['turno'].max() + 1) if not h_df.empty else 1
    
    # Reconstruir histórico para os gráficos
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    
    if not h_df.empty:
        for t in range(1, int(h_df['turno'].max() + 1)):
            turno_data = h_df[h_df['turno'] == t]
            st.session_state.historico.append({**{"Turno": t}, **dict(zip(turno_data['nome'], turno_data['pontos_resultantes']))})
            st.session_state.historico_acoes.append(dict(zip(turno_data['nome'], turno_data['acao'])))
            
    st.session_state.init = True

# =====================================================
# LÓGICA DE JOGO
# =====================================================

def adicionar():
    nome = st.session_state.novo_nome
    if nome:
        salvar_jogador_db(nome, 10, len(st.session_state.jogadores)+1, False)
        st.session_state.jogadores.append({"nome": nome, "pontos": 10, "ordem": len(st.session_state.jogadores)+1, "pago": False})
        st.session_state.novo_nome = ""

def finalizar_turno():
    vencedores = [j["nome"] for j in st.session_state.jogadores if st.session_state.get(f"sel_{j['nome']}") == "Venceu"]
    if len(vencedores) != 1:
        st.error("Selecione exatamente 1 vencedor.")
        return

    linha_pontos = {"Turno": st.session_state.turno}
    linha_acoes = {}

    for j in st.session_state.jogadores:
        nome = j["nome"]
        acao = st.session_state.get(f"sel_{nome}") or "Desistiu"
        
        if acao == "Perdeu": j["pontos"] -= 2
        elif acao == "Desistiu": j["pontos"] -= 1
        j["pontos"] = max(j["pontos"], 0)
        
        # SALVAR NO BANCO DE DADOS (SQL)
        registrar_turno_db(st.session_state.turno, nome, j["pontos"], acao)
        salvar_jogador_db(j["nome"], j["pontos"], j["ordem"], j["pago"])
        
        linha_pontos[nome] = j["pontos"]
        linha_acoes[nome] = acao
        st.session_state[f"sel_{nome}"] = None # Reset visual da ação

    st.session_state.historico.append(linha_pontos)
    st.session_state.historico_acoes.append(linha_acoes)
    st.session_state.turno += 1

# =====================================================
# UI
# =====================================================

st.title("🃏 CACHETA SQL DATABASE")

# CSS para centralização e cabeçalhos
st.markdown("""<style>
    .stTable td, .stTable th { text-align: center !important; vertical-align: middle !important; height: 60px !important; }
    .stTable th { color: white !important; background-color: #0E1117 !important; }
</style>""", unsafe_allow_html=True)

with st.expander("👤 Gerenciar Jogadores"):
    c1, c2 = st.columns([3,1])
    c1.text_input("Nome", key="novo_nome")
    c2.button("Adicionar", on_click=adicionar)

st.markdown("---")
h = st.columns([2, 1, 2, 1, 1])
cols = ["Jogador", "Ordem", "Resultado", "Pago?", "Ação"]
for i, col in enumerate(h): col.write(f"**{cols[i]}**")

for j in st.session_state.jogadores:
    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
    c1.write(j["nome"])
    j["ordem"] = c2.number_input("", value=j["ordem"], key=f"ord_{j['nome']}", label_visibility="collapsed")
    c3.selectbox("", [None, "Venceu", "Perdeu", "Desistiu"], key=f"sel_{j['nome']}", label_visibility="collapsed")
    
    # Pagamento Persistente no SQL
    novo_pago = c4.checkbox("Sim", value=j["pago"], key=f"pago_{j['nome']}")
    if novo_pago != j["pago"]:
        j["pago"] = novo_pago
        salvar_jogador_db(j["nome"], j["pontos"], j["ordem"], j["pago"])

    if c5.button("🗑", key=f"del_{j['nome']}"):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM jogadores WHERE nome = ?", (j["nome"],))
        conn.commit()
        conn.close()
        st.rerun()

st.button("✅ Finalizar Turno", on_click=finalizar_turno, use_container_width=True)
if st.button("🔄 Novo Jogo", use_container_width=True):
    limpar_banco_novo_jogo()
    st.rerun()

# =====================================================
# TABELA E GRÁFICO
# =====================================================

if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico).set_index("Turno")
    ac = pd.DataFrame(st.session_state.historico_acoes)
    
    def style_cacheta(styler):
        for i in range(len(df)):
            max_v = df.iloc[i].max()
            for col in df.columns:
                acao = ac.iloc[i][col]
                bg = "#f1c40f"; tx = "black"
                if acao == "Venceu": bg = "#2ecc71"; tx = "white"
                elif acao == "Perdeu": bg = "#e74c3c"; tx = "white"
                
                est = {"background-color": bg, "color": tx, "font-weight": "bold"}
                if df.iloc[i][col] == max_v and max_v > 0:
                    est["border"] = "4px solid #00ff00"; est["border-radius"] = "10px"
                if df.iloc[i][col] in [1, 2]: est["color"] = "#FF0000"
                
                styler.set_properties(subset=pd.IndexSlice[[df.index[i]], [col]], **est)
        return styler

    st.table(df.astype(str).replace(["0", "0.0"], "X").style.pipe(style_cacheta))
    st.plotly_chart(px.line(df.reset_index().melt(id_vars="Turno"), x="Turno", y="value", color="variable", markers=True))
