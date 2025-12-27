import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import wave
import os
from uncertainties import ufloat

# --- FUNÇÃO DE ANÁLISE OTIMIZADA ---
def analisar_audio(filename, dist_val, dist_err, temp_val, temp_err, sensibilidade_impacto=0.1):
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

        # 2. Cortar (Limite 10s)
        limit_sec = 10.0
        if len(signal) > limit_sec * fps:
            signal = signal[:int(limit_sec * fps)]
        
        signal_full = signal
        time_full = np.linspace(0, len(signal)/fps, num=len(signal))

        # 3. Achar o TIRO (Máximo Absoluto Global)
        abs_signal = np.abs(signal_full)
        idx_tiro = np.argmax(abs_signal)
        
        # Validação de ruído mínimo
        if abs_signal[idx_tiro] < 0.05:
            return None, "Som muito baixo. Não detectei o disparo."

        t_tiro = time_full[idx_tiro]
        amp_tiro = signal_full[idx_tiro]

        # 4. Janela de Busca (Física)
        c_som = 331.4 + (0.6 * temperatura.n)
        d_val = distancia.n
        
        # Velocidades esperadas (ajustável se necessário, mas 40-1000 cobre tudo)
        v_min = 40.0   # Paintball/Airsoft lento
        v_max = 1000.0 # Rifle de alta velocidade
        
        # Tempo desde o tiro ATÉ o som do impacto chegar no microfone
        # dt_mic = t_voo + t_som_retorno
        # dt_mic = (d/v) + (d/c)
        
        dt_min_teorico = (d_val / v_max) + (d_val / c_som)
        dt_max_teorico = (d_val / v_min) + (d_val / c_som)
        
        idx_min = idx_tiro + int(dt_min_teorico * fps)
        idx_max = idx_tiro + int(dt_max_teorico * fps)
        
        if idx_min >= len(signal_full):
            return None, "Áudio curto demais ou distância muito grande."
        
        # Ajusta final da janela se passar do áudio
        idx_max = min(idx_max, len(signal_full))

        # 5. Achar o IMPACTO (find_peaks na Janela)
        segmento = abs_signal[idx_min:idx_max]
        
        # Sensibilidade: O pico do impacto deve ser pelo menos X% do pico do tiro
        min_height = abs_signal[idx_tiro] * sensibilidade_impacto
        
        # Distância mínima entre picos (evita pegar o ringing do próprio tiro)
        min_dist = int(fps * 0.005) # 5ms
        
        picos, properties = find_peaks(segmento, height=min_height, distance=min_dist)
        
        idx_impacto = -1
        msg_erro = None
        
        if len(picos) == 0:
            # Nenhum pico relevante encontrado na janela física
            # Pode ser que não houve impacto, ou foi muito baixo.
            msg_erro = "Nenhum impacto detectado na janela esperada."
        else:
            # Pega o primeiro pico forte que obedece a física
            # Geralmente o PRIMEIRO pico na janela válida é o impacto direto.
            # O resto pode ser eco.
            idx_local = picos[0] 
            idx_impacto = idx_min + idx_local
        
        # 6. GERAR FIGURA (Mesmo se der erro, pra debug)
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Define zoom visual
        pad = int(0.1 * fps) # 100ms de margem
        p_plot_start = max(0, idx_tiro - pad)
        p_plot_end = min(len(signal_full), idx_max + pad)
        
        time_plot = time_full[p_plot_start:p_plot_end]
        sig_plot = signal_full[p_plot_start:p_plot_end]
        
        ax.plot(time_plot, sig_plot, color='#2196F3', lw=1, label="Sinal de Áudio")
        
        # Marcar Tiro
        ax.plot(t_tiro, amp_tiro, "rx", markersize=12)
        ax.annotate("Tiro", (t_tiro, amp_tiro), xytext=(0, 10), textcoords='offset points', ha='center', color='red')

        # Desenhar Janela de Busca (Área Verde Clara)
        t_janela_inicio = time_full[idx_min]
        t_janela_fim = time_full[idx_max-1] if idx_max > idx_min else t_janela_inicio
        ax.axvspan(t_janela_inicio, t_janela_fim, color='green', alpha=0.1, label="Janela Física Válida")
        
        if idx_impacto != -1:
            t_impacto = time_full[idx_impacto]
            amp_impacto = signal_full[idx_impacto]
            
            ax.plot(t_impacto, amp_impacto, "ro", markersize=8)
            ax.annotate("Impacto", (t_impacto, amp_impacto), xytext=(0, 15), textcoords='offset points', ha='center', color='red', fontweight='bold')
            
            # Linha conectando os picos
            # ax.hlines(y=amp_impacto, xmin=t_tiro, xmax=t_impacto, linestyles='dotted', colors='gray')

            # --- CÁLCULOS FINAIS ---
            delta_t_mic = ufloat(t_impacto - t_tiro, 1/fps)
            c_som_u = 331.4 + (0.6 * temperatura)
            t_voo = delta_t_mic - (distancia / c_som_u)
            
            if t_voo.n > 0:
                v_bala = distancia / t_voo
                results['v_bala'] = v_bala
                results['delta_t'] = delta_t_mic
                ax.set_title(f"Velocidade: {v_bala.n:.1f} +/- {v_bala.s:.1f} m/s", fontsize=14, color='green')
            else:
                ax.set_title("Erro: Tempo de voo negativo (Física Impossível)", color='red')
                msg_erro = "Cálculo resultou em tempo negativo."

        else:
             ax.set_title(f"Impacto não encontrado (Aumente a sensibilidade?)", color='orange')

        ax.set_xlabel("Tempo (s)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        plt.tight_layout()
        
        if msg_erro:
            return None, msg_erro, fig # Retorna erro E figura pra debug
            
        return results, None, fig # Sucesso

    except Exception as e:
        return None, f"Erro Interno: {str(e)}", None