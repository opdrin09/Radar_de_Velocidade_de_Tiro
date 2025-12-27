import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import wave
import os
from uncertainties import ufloat

# --- FUNÇÃO DE ANÁLISE (Backend Otimizado) ---
def analisar_audio(filename, dist_val, dist_err, temp_val, temp_err):
    results = {}
    
    if not filename or not os.path.exists(filename):
        return None, "Arquivo inexistente."

    try:
        # Variáveis com incerteza
        distancia = ufloat(dist_val, dist_err)
        temperatura = ufloat(temp_val, temp_err)

        # 1. LEITURA NATIVA DE WAV
        try:
            with wave.open(filename, 'rb') as wf:
                framerate = wf.getframerate()
                nframes = wf.getnframes()
                channels = wf.getnchannels()
                raw_data = wf.readframes(nframes)
                signal_raw = np.frombuffer(raw_data, dtype=np.int16)
                if channels > 1:
                    signal_raw = signal_raw[::channels]
                signal = signal_raw / 32768.0
                fps = framerate
        except wave.Error:
            return None, "Formato inválido. Use arquivos WAV."

        # 2. Cortar (Limite 10s para garantir performance na web)
        limit_sec = 10.0
        if len(signal) > limit_sec * fps:
            signal = signal[:int(limit_sec * fps)]
        
        signal_full = signal
        time_full = np.linspace(0, len(signal)/fps, num=len(signal))

        # 3. Achar o TIRO (Máximo Absoluto)
        abs_signal = np.abs(signal_full)
        idx_tiro = np.argmax(abs_signal)
        
        # Validação simples de ruído
        if abs_signal[idx_tiro] < 0.05:
            return None, "Som muito baixo. Não detectei tiro claro."

        t_tiro = time_full[idx_tiro]
        amp_tiro = signal_full[idx_tiro]

        # 4. Janela de Busca (Física)
        c_som = 331.4 + (0.6 * temperatura.n)
        d_val = distancia.n
        
        dt_min = (d_val / 350.0) + (d_val / c_som)
        dt_max = (d_val / 40.0) + (d_val / c_som)
        
        idx_min = idx_tiro + int(dt_min * fps)
        idx_max = idx_tiro + int(dt_max * fps)
        
        if idx_min >= len(signal_full):
            return None, "Áudio curto demais, acabou antes do impacto esperado."
        idx_max = min(idx_max, len(signal_full))

        # 5. Achar o IMPACTO (SCIPY find_peaks)
        # Agora podemos usar SCIPY à vontade, pois rodará na nuvem!
        segmento = abs_signal[idx_min:idx_max]
        
        # Parâmetros robustos
        # height: Mínimo 10% da altura do tiro
        # distance: Picos devem estar separados por pelo menos 10ms
        picos, properties = find_peaks(segmento, height=abs_signal[idx_tiro] * 0.1, distance=int(fps * 0.01))
        
        if len(picos) == 0:
            # Fallback: máximo local se find_peaks falhar
            idx_local = np.argmax(segmento)
        else:
            # Pega o pico mais alto encontrado (maior 'peak_heights')
            idx_pico_forte = np.argmax(properties['peak_heights'])
            idx_local = picos[idx_pico_forte]
            
        idx_impacto = idx_min + idx_local
        
        # Validação extra de amplitude
        if abs_signal[idx_impacto] < (abs_signal[idx_tiro] * 0.05):
             return None, "Impacto muito fraco detectado (ruído?)."

        t_impacto = time_full[idx_impacto]
        amp_impacto = signal_full[idx_impacto]

        # 6. CÁLCULOS
        delta_t_mic = ufloat(t_impacto - t_tiro, 1/fps)
        c_som_u = 331.4 + (0.6 * temperatura)
        t_voo = delta_t_mic - (distancia / c_som_u)
        
        if t_voo.n <= 0:
            return None, f"Erro físico: Tempo de voo negativo ({t_voo.n*1000:.1f}ms)."

        v_bala = distancia / t_voo

        results['delta_t'] = delta_t_mic
        results['v_bala'] = v_bala

        # 7. GERAR FIGURA MATPLOTLIB (Para Streamlit)
        # Não salvamos arquivo, retornamos o objeto Figure
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Zoom inteligente
        pad = int(0.05 * fps)
        p_start = max(0, idx_tiro - pad)
        p_end = min(len(signal_full), idx_impacto + pad)
        
        ax.plot(time_full[p_start:p_end], signal_full[p_start:p_end], color='#2196F3', lw=1, label="Audio Waveform")
        ax.plot([t_tiro, t_impacto], [amp_tiro, amp_impacto], "rx", markersize=10, label="Events (Shot/Impact)")
        
        # Anotações
        ax.annotate(f"Tiro\n{t_tiro:.3f}s", xy=(t_tiro, amp_tiro), xytext=(t_tiro, amp_tiro+0.1), 
                    arrowprops=dict(facecolor='black', shrink=0.05), ha='center')
        ax.annotate(f"Impacto\n{t_impacto:.3f}s", xy=(t_impacto, amp_impacto), xytext=(t_impacto, amp_impacto+0.1), 
                    arrowprops=dict(facecolor='black', shrink=0.05), ha='center')

        ax.set_title(f"Velocidade Calculada: {v_bala.n:.1f} +/- {v_bala.s:.1f} m/s")
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude")
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()

        # Retornamos dict de resultados e a FIGURA
        return results, fig

    except Exception as e:
        return None, f"Erro Interno: {str(e)}"