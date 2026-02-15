import streamlit as st

st.set_page_config(page_title="CACHETA", layout="centered")

if "jogadores" not in st.session_state:
    st.session_state.jogadores = []

st.title("CACHETA")

nome = st.text_input("Jogador")

if st.button("Adicionar"):
    if nome:
        st.session_state.jogadores.append({
            "nome": nome,
            "pontos": 10,
            "v":0,"d":0,"a":0,"j":0,"e":False
        })

for j in st.session_state.jogadores:
    if not j["e"]:
        st.subheader(f'{j["nome"]} — {j["pontos"]} pts')
        c1,c2 = st.columns(2)
        if c1.button(f'🏆 {j["nome"]}'):
            j["v"]+=1
        if c2.button(f'❌ {j["nome"]}'):
            j["d"]+=1
            if j["pontos"]<=2:
                j["e"]=True
            else:
                j["pontos"]-=2
    else:
        st.write(f'{j["nome"]} ELIMINADO')

if st.button("Restante não foi"):
    for j in st.session_state.jogadores:
        if not j["e"]:
            j["a"]+=1
            j["pontos"]-=1

if st.button("Novo jogo"):
    for j in st.session_state.jogadores:
        j["pontos"]=10
        j["e"]=False
