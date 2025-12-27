import streamlit as st
import os
import tempfile
from analise_audio import analisar_audio

# Configuração da Página
st.set_page_config(page_title="Balística APP", page_icon="🎯", layout="centered")

st.title("🎯 Medidor de Velocidade de Projétil")
st.markdown("""
Esta aplicação calcula a velocidade da bala baseada no som do disparo e do impacto.
Use o gravador abaixo ou faça upload de uma gravação.
""")

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

# 1. Componente de Upload
arquivo = st.file_uploader("Envie um arquivo WAV", type=["wav", "mp3", "m4a"])

# 2. Componente de Gravação (Se disponível no navegador)
# Nota: st.audio_input é recente. Se der erro, usamos apenas upload.
audio_buffer = None

if arquivo:
    audio_buffer = arquivo
else:
    # Tenta usar o experimental audio input se disponível
    try:
        gravacao = st.audio_input("Ou grave agora:")
        if gravacao:
            audio_buffer = gravacao
    except:
        st.info("Gravação via navegador não suportada nesta versão. Use o Upload.")

# --- PROCESSAMENTO ---
if audio_buffer is not None:
    st.success("Áudio carregado! Analisando...")
    
    # Salvar temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_buffer.getvalue())
        tmp_filename = tmp_file.name

    # Chamar análise
    # Streamlit roda num servidor potente, então vai ser rápido!
    with st.spinner('Processando física do disparo...'):
        resultados, figura = analisar_audio(tmp_filename, dist_val, dist_err, temp_val, temp_err)

    # Exibir Resultados
    if resultados:
        st.divider()
        v = resultados['v_bala']
        
        # Display Gigante da Velocidade
        st.metric(label="Velocidade da Bala", value=f"{v.n:.1f} m/s", delta=f"± {v.s:.1f} m/s")
        
        st.write(f"⏱️ **Delta T (Mic):** {resultados['delta_t']:.4f} s")
        
        # Mostrar o Gráfico
        if figura:
            st.pyplot(figura)
            
    else:
        st.error(f"Erro na análise: {figura}") # Figura contem msg de erro nesse caso
    
    # Limpeza
    os.unlink(tmp_filename)
