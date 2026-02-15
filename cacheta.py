import streamlit as st
import pandas as pd
import plotly.express as px
import json, os

st.set_page_config(page_title="CACHETA", layout="wide")

ARQ = "cacheta_state.json"

# =========================
# PERSISTÊNCIA
# =========================

def salvar_estado():
    with open(ARQ,"w") as f:
        json.dump({
            "jogadores": st.session_state.jogadores,
            "turno": st.session_state.turno,
            "historico_turnos": st.session_state.historico_turnos,
            "historico_acoes": st.session_state.historico_acoes,
            "stats": st.session_state.stats
        },f)

def carregar_estado():
    if os.path.exists(ARQ):
        with open(ARQ) as f:
            d=json.load(f)
            st.session_state.jogadores=d.get("jogadores",[])
            st.session_state.turno=d.get("turno",1)
            st.session_state.historico_turnos=d.get("historico_turnos",[])
            st.session_state.historico_acoes=d.get("historico_acoes",[])
            st.session_state.stats=d.get("stats",{})

# =========================
# INIT
# =========================

if "init" not in st.session_state:
    st.session_state.init=True
    st.session_state.jogadores=[]
    st.session_state.turno=1
    st.session_state.acoes={}
    st.session_state.historico_turnos=[]
    st.session_state.historico_acoes=[]
    st.session_state.stats={}
    carregar_estado()

# =========================
# FUNÇÕES
# =========================

def adicionar():
    nome=st.session_state.novo_nome
    if not nome:return
    st.session_state.jogadores.append({"nome":nome,"pontos":10,"ordem":len(st.session_state.jogadores)+1})
    st.session_state.stats.setdefault(nome,{"turnos":0,"vitorias":0,"derrotas":0,"desistencias":0})
    st.session_state.novo_nome=""
    salvar_estado()

def excluir(nome):
    st.session_state.jogadores=[j for j in st.session_state.jogadores if j["nome"]!=nome]
    salvar_estado()

def limpar_radios():
    for j in st.session_state.jogadores:
        k=f"acao_{j['nome']}"
        if k in st.session_state: del st.session_state[k]
    st.session_state.acoes={}

def selecionar(nome,acao):
    if acao=="Venceu":
        for k in st.session_state.acoes:
            if st.session_state.acoes[k]=="Venceu":
                st.session_state.acoes[k]=""
    st.session_state.acoes[nome]=acao

def finalizar():

    if list(st.session_state.acoes.values()).count("Venceu")!=1:
        st.warning("Selecione exatamente 1 vencedor.")
        return

    lp={"Turno":st.session_state.turno}
    la={}

    for j in st.session_state.jogadores:
        n=j["nome"]
        a=st.session_state.acoes.get(n,"Desistiu")

        st.session_state.stats[n]["turnos"]+=1

        if a=="Perdeu": j["pontos"]-=2
        elif a=="Desistiu": j["pontos"]-=1

        j["pontos"]=max(j["pontos"],0)
        lp[n]=j["pontos"]
        la[n]=a

    st.session_state.historico_turnos.append(lp)
    st.session_state.historico_acoes.append(la)

    st.session_state.turno+=1
    limpar_radios()
    salvar_estado()

def novo_jogo():
    for j in st.session_state.jogadores:j["pontos"]=10
    st.session_state.turno=1
    st.session_state.historico_turnos=[]
    st.session_state.historico_acoes=[]
    limpar_radios()
    salvar_estado()

# =========================
# UI
# =========================

st.title("CACHETA")

st.text_input("Adicionar jogador",key="novo_nome")
st.button("Adicionar",on_click=adicionar)

st.subheader(f"Turno {st.session_state.turno}")

# Cabeçalho tipo tabela
h1,h2,h3,h4=st.columns([3,1,4,1])
h1.markdown("**Jogador**")
h2.markdown("**Ordem**")
h3.markdown("**Resultado do Turno**")
h4.markdown("**Excluir**")

for j in sorted(st.session_state.jogadores,key=lambda x:x["ordem"]):

    c1,c2,c3,c4=st.columns([3,1,4,1])

    c1.write(j["nome"])
    j["ordem"]=c2.number_input("",value=j["ordem"],key=j["nome"]+"_ord",label_visibility="collapsed")

    esc=c3.radio("",["","Venceu","Perdeu"],horizontal=True,key=f"acao_{j['nome']}")
    if esc: selecionar(j["nome"],esc)

    if c4.button("🗑",key=j["nome"]+"x"):
        excluir(j["nome"])
        st.experimental_rerun()

a,b,c=st.columns(3)
a.button("Finalizar Turno",on_click=finalizar)
b.button("Reiniciar Turno",on_click=limpar_radios)
c.button("Novo Jogo",on_click=novo_jogo)

# =========================
# PLACAR COLORIDO
# =========================

if st.session_state.historico_turnos:

    df=pd.DataFrame(st.session_state.historico_turnos).set_index("Turno")
    ac=pd.DataFrame(st.session_state.historico_acoes)

    sty=df.style

    for i in range(len(df)):
        for col in df.columns:
            cor="#f1c40f"
            if ac.iloc[i][col]=="Venceu":cor="#2ecc71"
            if ac.iloc[i][col]=="Perdeu":cor="#e74c3c"
            sty=sty.set_properties(subset=pd.IndexSlice[[df.index[i]],[col]],**{"background-color":cor,"color":"black","font-weight":"bold"})

    st.subheader("Placar por Turnos")
    st.dataframe(sty,use_container_width=True)

    dm=df.reset_index().melt(id_vars="Turno",var_name="Jogador",value_name="Pontos")
    st.plotly_chart(px.line(dm,x="Turno",y="Pontos",color="Jogador",markers=True),use_container_width=True)
