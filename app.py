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
    
    st.subheader("Filtros de Detecção")
    
    # Sensibilidade: Agora com input numérico para precisão (0 a 100)
    sensibilidade = st.number_input("Sensibilidade do Impacto (0-100%)", min_value=1.0, max_value=100.0, value=10.0, step=0.5, format="%.1f", help="Porcentagem da altura do pico do impacto em relação ao tiro.")
    
    st.subheader("Range de Velocidade (m/s)")
    v_min_input = st.number_input("Mínima", value=40.0, step=10.0, help="Velocidade mínima esperada para o projétil.")
    v_max_input = st.number_input("Máxima", value=1000.0, step=50.0, help="Velocidade máxima possível.")
    
    st.info(f"O impacto deve ser pelo menos {sensibilidade}% da altura do tiro.")

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
    # 0. Tocar o áudio (Para o usuário validar)
    st.audio(buffer_final)
    
    # Salvar temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(buffer_final.getvalue())
        tmp_filename = tmp_file.name

    with st.spinner('Analisando física...'):
        # Passamos a sensibilidade convertida para decimal
        res, msg_erro, figuras = analisar_audio(
            tmp_filename, 
            dist_val, dist_err, 
            temp_val, temp_err, 
            sensibilidade_impacto=sensibilidade/100.0,
            v_min=v_min_input,
            v_max=v_max_input
        )
        
        # Desempacota figuras (se existirem)
        if figuras and figuras[0] is not None:
            fig_full, fig_zoom = figuras
        else:
            fig_full, fig_zoom = None, None

    # 1. Gráfico Geral (Visualização da Onda Completa - Pedido do Usuário)
    if fig_full:
        st.subheader("1. Visão Geral (Áudio Completo)")
        st.pyplot(fig_full)

    # 2. Gráfico de Zoom (Otimizado)
    if fig_zoom:
        st.subheader("2. Detalhe da Captura (Zoom)")
        st.pyplot(fig_zoom)

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
