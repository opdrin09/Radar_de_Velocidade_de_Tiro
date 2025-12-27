import streamlit as st
import os
import tempfile
import matplotlib.pyplot as plt
from analise_audio import analisar_audio

# Configuração da Página
st.set_page_config(page_title="Balística APP", page_icon="🎯", layout="centered")

st.title("🎯 Medidor de Velocidade")

# Sidebar de Ajuda
with st.sidebar:
    st.header("⚙️ Configurações")
    sensibilidade = st.slider("Sensibilidade do Impacto (%)", min_value=1, max_value=50, value=10, step=1, help="Porcentagem da altura do pico do impacto em relação ao tiro. Se tiver muito ruído/eco, aumente este valor.")
    st.info(f"O impacto deve ser pelo menos {sensibilidade}% da altura do tiro para ser detectado.")

# --- INPUTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distância (m)")
    dist_val = st.number_input("Valor", min_value=1.0, value=50.0, step=1.0)
    dist_err = st.number_input("Incerteza +/-", min_value=0.0, value=0.5, step=0.1)

with col2:
    st.subheader("Temperatura (°C)")
    temp_val = st.number_input("Valor", min_value=-20.0, value=25.0, step=1.0)
    temp_err = st.number_input("Incerteza +/-", min_value=0.0, value=2.0, step=0.5)

# --- ÁUDIO ---
st.divider()
st.subheader("🔊 Arquivo de Áudio")

arquivo = st.file_uploader("Envie um arquivo WAV", type=["wav", "mp3", "m4a"])

# Seção de gravação nativa (experimental)
st.caption("Ou grave direto no navegador:")
audio_gravado = st.audio_input("Microfone")

buffer_final = None
if audio_gravado:
    buffer_final = audio_gravado
elif arquivo:
    buffer_final = arquivo

# --- PROCESSAMENTO ---
if buffer_final is not None:
    # Salvar temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(buffer_final.getvalue())
        tmp_filename = tmp_file.name

    with st.spinner('Analisando física...'):
        # Passamos a sensibilidade convertida para decimal (10% -> 0.1)
        res, msg_erro, figura = analisar_audio(tmp_filename, dist_val, dist_err, temp_val, temp_err, sensibilidade_impacto=sensibilidade/100.0)

    # Exibir Gráfico (Sempre exibir, mesmo com erro, para debug)
    if figura:
        st.pyplot(figura)

    # Exibir Resultados
    if res:
        st.divider()
        v = res['v_bala']
        st.success("Cálculo realizado com sucesso!")
        st.metric(label="Velocidade da Bala", value=f"{v.n:.1f} m/s", delta=f"± {v.s:.1f} m/s")
        st.write(f"⏱️ **Delta T (Mic):** {res['delta_t']:.4f} s")
    else:
        st.warning(f"Atenção: {msg_erro}")
        st.markdown("""
        **Dicas:**
        - Verifique se a **Janela Verde** no gráfico cobre onde o impacto deveria estar.
        - Se pegou um **ECO** (pico errado), tente aumentar a **Sensibilidade** na barra lateral esquerda.
        - Se não pegou **NADA**, diminua a Sensibilidade.
        """)
    
    # Limpeza
    os.unlink(tmp_filename)
