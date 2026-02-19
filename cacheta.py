import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="CACHETA CLOUD - FLÁVIO", layout="wide")

# =====================================================
# CONEXÃO E CSS
# =====================================================

# Injeta CSS para centralização e cabeçalhos brancos
st.markdown("""
    <style>
    .stTable td, .stTable th { text-align: center !important; vertical-align: middle !important; height: 60px !important; }
    .stTable th { color: white !important; background-color: #0E1117 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# Estabelece conexão com o Google Sheets
# Nota: A URL da planilha deve estar nos Secrets do Streamlit como 'spreadsheet'
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df_j = conn.read(worksheet="jogadores", ttl=0)
        df_h = conn.read(worksheet="historico", ttl=0)
        return df_j, df_h
    except:
        # Cria dataframes vazios se as abas não existirem ou estiverem vazias
        df_j = pd.DataFrame(columns=["nome", "pontos", "ordem", "pago"])
        df_h = pd.DataFrame(columns=["turno", "nome", "pontos_resultantes", "acao"])
        return df_j, df_h

# =====================================================
# NAVEGAÇÃO
# =====================================================

st.sidebar.title("🎮 Menu Cacheta")
tela = st.sidebar.radio("Navegação:", ["Partida Atual", "Estatísticas Históricas"])

df_jogadores, df_historico = carregar_dados()

# =====================================================
# TELA 1: PARTIDA ATUAL
# =====================================================

if tela == "Partida Atual":
    st.title("🃏 Jogo em Andamento (Google Sheets)")

    with st.expander("👤 Gerenciar Jogadores"):
        c_a1, c_a2 = st.columns([3, 1])
        nome_novo = c_a1.text_input("Nome do jogador")
        if c_a2.button("Adicionar") and nome_novo:
            if nome_novo not in df_jogadores['nome'].values:
                novo_j = pd.DataFrame([{"nome": nome_novo, "pontos": 10, "ordem": len(df_jogadores)+1, "pago": False}])
                df_atualizado = pd.concat([df_jogadores, novo_j], ignore_index=True)
                conn.update(worksheet="jogadores", data=df_atualizado)
                st.success(f"{nome_novo} adicionado!")
                st.rerun()

    # Filtra jogadores ativos (que não foram excluídos)
    if not df_jogadores.empty:
        st.markdown("---")
        h = st.columns([2, 1, 2, 1, 1])
        for col_header, t in zip(h, ["Jogador", "Ordem", "Resultado", "Pago?", "Ação"]):
            col_header.write(f"**{t}**")

        df_jogadores = df_jogadores.sort_values("ordem")
        
        for idx, row in df_jogadores.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
            c1.write(f"**{row['nome']}**")
            
            # Ordem
            nova_ord = c2.number_input("", value=int(row['ordem']), key=f"ord_{row['nome']}", label_visibility="collapsed")
            if nova_ord != row['ordem']:
                df_jogadores.at[idx, 'ordem'] = nova_ord
                conn.update(worksheet="jogadores", data=df_jogadores)

            # Ação do Turno (Apenas no Session State, não vai pra planilha até o fim do turno)
            st.selectbox("", [None, "Venceu", "Perdeu", "Desistiu"], key=f"sel_{row['nome']}", label_visibility="collapsed")

            # Pago
            pago_val = bool(row['pago'])
            novo_pago = c4.checkbox("Sim", value=pago_val, key=f"p_{row['nome']}")
            if novo_pago != pago_val:
                df_jogadores.at[idx, 'pago'] = novo_pago
                conn.update(worksheet="jogadores", data=df_jogadores)

            if c5.button("🗑", key=f"del_{row['nome']}"):
                df_jogadores = df_jogadores.drop(idx)
                conn.update(worksheet="jogadores", data=df_jogadores)
                st.rerun()

        # Finalizar Turno
        if st.button("✅ Finalizar Turno", use_container_width=True):
            vencedores = [n for n in df_jogadores['nome'] if st.session_state.get(f"sel_{n}") == "Venceu"]
            
            if len(vencedores) != 1:
                st.error("Selecione exatamente 1 vencedor.")
            else:
                proximo_turno = int(df_historico['turno'].max() + 1) if not df_historico.empty else 1
                novas_linhas_h = []

                for idx, row in df_jogadores.iterrows():
                    acao = st.session_state.get(f"sel_{row['nome']}") or "Desistiu"
                    pts_atuais = int(row['pontos'])
                    
                    if acao == "Perdeu": pts_atuais -= 2
                    elif acao == "Desistiu": pts_atuais -= 1
                    pts_atuais = max(pts_atuais, 0)

                    df_jogadores.at[idx, 'pontos'] = pts_atuais
                    novas_linhas_h.append({
                        "turno": proximo_turno,
                        "nome": row['nome'],
                        "pontos_resultantes": pts_atuais,
                        "acao": acao
                    })
                
                # Sobe as atualizações para o Google Sheets
                df_historico_new = pd.concat([df_historico, pd.DataFrame(novas_linhas_h)], ignore_index=True)
                conn.update(worksheet="jogadores", data=df_jogadores)
                conn.update(worksheet="historico", data=df_historico_new)
                st.success(f"Turno {proximo_turno} finalizado!")
                st.rerun()

        if st.button("🔄 Novo Jogo", use_container_width=True):
            df_jogadores['pontos'] = 10
            df_jogadores['pago'] = False
            # Aqui você escolhe se limpa o histórico da planilha ou não. 
            # Para manter estatísticas, NÃO limpe o df_historico.
            conn.update(worksheet="jogadores", data=df_jogadores)
            st.rerun()

    # Exibição do Placar Visual (Lendo do histórico da Planilha)
    if not df_historico.empty:
        st.markdown("---")
        st.subheader("📊 Placar Histórico (Google Sheets)")
        
        # Pivotar para o formato de tabela
        df_p = df_historico.pivot(index='turno', columns='nome', values='pontos_resultantes')
        df_a = df_historico.pivot(index='turno', columns='nome', values='acao')
        
        def style_gsheets(styler):
            for i in range(len(df_p)):
                max_v = df_p.iloc[i].max()
                for col in df_p.columns:
                    acao = df_a.iloc[i][col]
                    pts = df_p.iloc[i][col]
                    bg = "#f1c40f"; tx = "black"
                    if acao == "Venceu": bg = "#2ecc71"; tx = "white"
                    elif acao == "Perdeu": bg = "#e74c3c"; tx = "white"
                    est = {"background-color": bg, "color": tx, "font-weight": "bold"}
                    if pts == max_v and max_v > 0:
                        est["border"] = "4px solid #00ff00"; est["border-radius"] = "10px"
                    if pts in [1, 2]: est["color"] = "#FF0000"; est["font-size"] = "1.2em"
                    styler.set_properties(subset=pd.IndexSlice[[df_p.index[i]], [col]], **est)
            return styler

        st.table(df_p.astype(str).replace(["0", "0.0"], "X").style.pipe(style_gsheets))

# =====================================================
# TELA 2: ESTATÍSTICAS
# =====================================================

elif tela == "Estatísticas Históricas":
    st.title("📊 Estatísticas Acumuladas")
    if not df_historico.empty:
        # Cálculos de performance
        stats = df_historico.groupby('nome')['acao'].value_counts().unstack(fill_value=0).reset_index()
        total_turnos = df_historico.groupby('nome').size().reset_index(name='Total')
        stats = stats.merge(total_turnos, on='nome')
        
        for col in ["Venceu", "Perdeu", "Desistiu"]:
            if col not in stats.columns: stats[col] = 0
            stats[f"% {col}"] = (stats[col] / stats['Total'] * 100).round(1)

        st.dataframe(stats.sort_values("Venceu", ascending=False), use_container_width=True, hide_index=True)
        
        fig = px.bar(stats, x='nome', y=['Venceu', 'Perdeu', 'Desistiu'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado histórico na planilha ainda.")
