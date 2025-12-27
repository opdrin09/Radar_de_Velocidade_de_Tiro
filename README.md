# Radar de Velocidade de Tiro 🎯

Este projeto utiliza análise de áudio para calcular a velocidade de projéteis (balas, airsoft, etc) medindo o intervalo de tempo entre o som do disparo e o som do impacto.

## 🚀 Como usar

Este projeto foi desenhado para rodar no **Streamlit Cloud**.

1. **Upload**: Suba um vídeo ou áudio (.wav, .mp4) contendo o som do tiro e do impacto.
2. **Parâmetros**: Informe a distância até o alvo e a temperatura ambiente.
3. **Resultado**: O app calcula a velocidade e mostra o gráfico da forma de onda.

## 🛠 Tecnologias

- **Python**: Linguagem principal.
- **Streamlit**: Interface Web.
- **Numpy & Scipy**: Processamento de sinais e detecção de picos.
- **Matplotlib**: Visualização de dados.

## 📦 Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```
