import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os

# Configuração da Página
st.set_page_config(page_title="CACHETA PRO - FLÁVIO", layout="wide")

DB_NAME = "cacheta_dados.db"

# =====================================================
# FUNÇÕES DE BANCO DE DADOS (SQLITE)
# =====================================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jogadores 
                 (nome TEXT PRIMARY KEY, pontos INTEGER, ordem INTEGER, pago BOOLEAN)''')
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

def limpar_banco_novo_jogo():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE jogadores SET pontos = 10, pago = 0")
    c.execute("DELETE FROM historico")
    conn.commit()
    conn.close()

# =====================================================
# INICIALIZAÇÃO E NAVEGAÇÃO
# =====================================================

init_db()

st.sidebar.title("🎮 Menu Cacheta")
tela = st.sidebar.radio("Navegação:", ["Partida Atual", "Estatísticas Históricas"])

# Carregamento de dados para o session_state
conn = sqlite3.connect(DB_NAME)
j_df = pd.read_sql_query("SELECT * FROM jogadores", conn)
h_df = pd.read_sql_query("SELECT * FROM historico", conn)
conn.close()

if "init" not in st.session_state:
    st.session_state.jogadores = j_df.to_dict('records')
    st.session_state.turno = int(h_df['turno'].max() + 1) if not h_df.empty else 1
    st.session_state.historico = []
    st.session_state.historico_acoes = []
    if not h_df.empty:
        for t in sorted(h_df['turno'].unique()):
            turno_data = h_df[h_df['turno'] == t]
            st.session_state.historico.append({**{"Turno": t}, **dict(zip(turno_data['nome'], turno_data['pontos_resultantes']))})
            st.session_state.historico_acoes.append(dict(zip(turno_data['nome'], turno_data['acao'])))
    st.session_state.init = True

# =====================================================
# TELA 1: PARTIDA ATUAL
# =====================================================

if tela == "Partida Atual":
    st.title("🃏 Jogo em Andamento")

    # CSS para centralização e cabeçalhos brancos
    st.markdown("""
        <style>
        .stTable td, .stTable th { text-align: center !important; vertical-align: middle !important; height: 60px !important; }
        .stTable th { color: white !important; background-color: #0E1117 !important; font-weight: bold !important; }
        </style>
        """, unsafe_allow_html=True)

    with st.expander("👤 Gerenciar Jogadores"):
        c_a1, c_a2 = st.columns([3, 1])
        nome_novo = c_a1.text_input("Nome", key="input_nome")
        if c_a2.button("Adicionar") and nome_novo:
            salvar_jogador_db(nome_novo, 10, len(st.session_state.jogadores)+1, False)
            st.rerun()

    # Tabela de inputs
    st.markdown("---")
    h = st.columns([2, 1, 2, 1, 1])
    titulos = ["Jogador", "Ordem", "Ação Turno", "Pago?", "Excluir"]
    for i, t in enumerate(h): t.write(f"**{titulos[i]}**")

    jogadores_ordenados = sorted(st.session_state.jogadores, key=lambda x: x["ordem"])
    
    for j in jogadores_ordenados:
        c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
        c1.write(f"**{j['nome']}**")
        
        # Ordem
        nova_ord = c2.number_input("", value=j["ordem"], key=f"o_{j['nome']}", label_visibility="collapsed")
        if nova_ord != j["ordem"]:
            j["ordem"] = nova_ord
            salvar_jogador_db(j["nome"], j["pontos"], j["ordem"], j["pago"])

        # Ação
        c3.selectbox("", [None, "Venceu", "Perdeu", "Desistiu"], key=f"sel_{j['nome']}", label_visibility="collapsed")

        # Pago (Persiste até novo jogo)
        foi_pago = c4.checkbox("Sim", value=j["pago"], key=f"p_{j['nome']}")
        if foi_pago != j["pago"]:
            j["pago"] = foi_pago
            salvar_jogador_db(j["nome"], j["pontos"], j["ordem"], j["pago"])

        if c5.button("🗑", key=f"d_{j['nome']}"):
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM jogadores WHERE nome=?", (j['nome'],)); conn.commit(); conn.close()
            st.rerun()

    # Botões de turno
    b1, b2 = st.columns(2)
    if b1.button("✅ Finalizar Turno", use_container_width=True):
        vencedores = [j["nome"] for j in st.session_state.jogadores if st.session_state.get(f"sel_{j['nome']}") == "Venceu"]
        if len(vencedores) != 1:
            st.error("Selecione 1 vencedor.")
        else:
            l_pontos = {"Turno": st.session_state.turno}
            l_acoes = {}
            for j in st.session_state.jogadores:
                acao = st.session_state.get(f"sel_{j['nome']}") or "Desistiu"
                if acao == "Perdeu": j["pontos"] -= 2
                elif acao == "Desistiu": j["pontos"] -= 1
                j["pontos"] = max(j["pontos"], 0)
                registrar_turno_db(st.session_state.turno, j["nome"], j["pontos"], acao)
                salvar_jogador_db(j["nome"], j["pontos"], j["ordem"], j["pago"])
                l_pontos[j["nome"]] = j["pontos"]
                l_acoes[j["nome"]] = acao
                st.session_state[f"sel_{j['nome']}"] = None # Reset ação
            st.session_state.historico.append(l_pontos)
            st.session_state.historico_acoes.append(l_acoes)
            st.session_state.turno += 1
            st.rerun()

    if b2.button("🔄 Novo Jogo / Reset Pagamentos", use_container_width=True):
        limpar_banco_novo_jogo()
        st.rerun()

    # Placar Visual
    if st.session_state.historico:
        st.markdown("---")
        df = pd.DataFrame(st.session_state.historico).set_index("Turno")
        ac_df = pd.DataFrame(st.session_state.historico_acoes)

        def style_placar(styler):
            for i in range(len(df)):
                max_l = df.iloc[i].max()
                for col in df.columns:
                    acao = ac_df.iloc[i][col]
                    pts = df.iloc[i][col]
                    bg = "#f1c40f"; tx = "black"
                    if acao == "Venceu": bg = "#2ecc71"; tx = "white"
                    elif acao == "Perdeu": bg = "#e74c3c"; tx = "white"
                    est = {"background-color": bg, "color": tx, "font-weight": "bold"}
                    if pts == max_l and max_l > 0:
                        est["border"] = "4px solid #00ff00"; est["border-radius"] = "10px"
                    if pts in [1, 2]: est["color"] = "#FF0000"; est["font-size"] = "1.2em"
                    styler.set_properties(subset=pd.IndexSlice[[df.index[i]], [col]], **est)
            return styler

        st.table(df.astype(str).replace(["0", "0.0"], "X").style.pipe(style_placar))
        st.plotly_chart(px.line(df.reset_index().melt(id_vars="Turno"), x="Turno", y="value", color="variable", markers=True), use_container_width=True)

# =====================================================
# TELA 2: ESTATÍSTICAS HISTÓRICAS
# =====================================================

elif tela == "Estatísticas Históricas":
    st.title("📊 Estatísticas Gerais")
    
    conn = sqlite3.connect(DB_NAME)
    q = """
    SELECT nome as Jogador, COUNT(*) as 'Total Turnos',
    SUM(CASE WHEN acao='Venceu' THEN 1 ELSE 0 END) as Vitórias,
    SUM(CASE WHEN acao='Perdeu' THEN 1 ELSE 0 END) as Derrotas,
    SUM(CASE WHEN acao='Desistiu' THEN 1 ELSE 0 END) as Desistências
    FROM historico GROUP BY nome
    """
    df_s = pd.read_sql_query(q, conn); conn.close()

    if not df_s.empty:
        df_s['% Vitórias'] = (df_s['Vitórias'] / df_s['Total Turnos'] * 100).round(1)
        df_s['% Derrotas'] = (df_s['Derrotas'] / df_s['Total Turnos'] * 100).round(1)
        df_s['% Desistências'] = (df_s['Desistências'] / df_s['Total Turnos'] * 100).round(1)

        m1, m2, m3 = st.columns(3)
        m1.metric("🏆 Maior Vencedor", df_s.loc[df_s['Vitórias'].idxmax()]['Jogador'], f"{int(df_s['Vitórias'].max())} vitórias")
        m2.metric("📉 Mais Derrotas", df_s.loc[df_s['Derrotas'].idxmax()]['Jogador'], f"{int(df_s['Derrotas'].max())} derrotas")
        m3.metric("🏃 Rei da Desistência", df_s.loc[df_s['Desistências'].idxmax()]['Jogador'], f"{int(df_s['Desistências'].max())} turnos")

        st.dataframe(df_s.sort_values('% Vitórias', ascending=False), use_container_width=True, hide_index=True)
        
        st.subheader("Gráfico de Comportamento")
        st.plotly_chart(px.bar(df_s, x='Jogador', y=['Vitórias', 'Derrotas', 'Desistências'], barmode='group'), use_container_width=True)
    else:
        st.info("Ainda não há dados no banco de dados.")
