import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.utils import platform
from kivy.core.window import Window

# Importa nossa lógica refatorada
import analise_audio
import os

# Configuração simples de janela para testes no PC
if platform not in ('android', 'ios'):
    Window.size = (400, 700)

class BalisticaApp(App):
    def build(self):
        self.title = "Calculadora Balística Pro"
        
        # Layout Principal com ScrollView para telas pequenas
        root = BoxLayout(orientation='vertical')
        
        # Conteúdo
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height')) # Auto-ajuste

        # --- SEÇÃO 1: CONFIGURAÇÃO ---
        # Distância + Incerteza
        box_dist = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        box_dist.add_widget(Label(text="Dist (m):", size_hint_x=0.25))
        self.input_dist = TextInput(text="5.0", multiline=False, input_filter='float', size_hint_x=0.25)
        box_dist.add_widget(self.input_dist)
        
        box_dist.add_widget(Label(text="+/-:", size_hint_x=0.2))
        self.input_dist_err = TextInput(text="0.05", multiline=False, input_filter='float', size_hint_x=0.3)
        box_dist.add_widget(self.input_dist_err)
        layout.add_widget(box_dist)
        
        # Temperatura + Incerteza
        box_temp = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        box_temp.add_widget(Label(text="Temp (°C):", size_hint_x=0.25))
        self.input_temp = TextInput(text="30.0", multiline=False, input_filter='float', size_hint_x=0.25)
        box_temp.add_widget(self.input_temp)
        
        box_temp.add_widget(Label(text="+/-:", size_hint_x=0.2))
        self.input_temp_err = TextInput(text="1.0", multiline=False, input_filter='float', size_hint_x=0.3)
        box_temp.add_widget(self.input_temp_err)
        layout.add_widget(box_temp)
        
        # --- SEÇÃO 2: GRAVAÇÃO E SELEÇÃO ---
        layout.add_widget(Label(text="--- Captura de Áudio ---", size_hint_y=None, height=30, color=(0.5, 0.8, 1, 1)))

        # Botão Gravar
        self.btn_gravar = Button(text="GRAVAR Áudio (In App)", size_hint_y=None, height=50, background_color=(0.8, 0, 0, 1))
        self.btn_gravar.bind(on_release=self.toggle_gravacao)
        layout.add_widget(self.btn_gravar)

        # Botão Selecionar Arquivo
        self.btn_select = Button(text="OU Selecionar Arquivo Existente", size_hint_y=None, height=50)
        self.btn_select.bind(on_release=self.escolher_arquivo)
        layout.add_widget(self.btn_select)
        
        # --- SEÇÃO 3: RESULTADOS ---
        self.lbl_status = Label(text="Pronto.", size_hint_y=None, height=60, markup=True)
        layout.add_widget(self.lbl_status)
        
        self.img_result = Image(allow_stretch=True, keep_ratio=True, size_hint_y=None, height=300)
        layout.add_widget(self.img_result)

        # Envolve em ScrollView para garantir que caiba em qualquer tela
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)
        root.add_widget(scroll)

        # Estado da gravação
        self.gravando = False
        self.arquivo_gravado = "rec_temp.wav" 
        
        return root

    def toggle_gravacao(self, instance):
        from plyer import audio
        
        if not self.gravando:
            try:
                if platform == 'android':
                    # Contexto do Android para pegar pasta de arquivos privada
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    activity = PythonActivity.mActivity
                    # getExternalFilesDir(None) retorna a pasta privada no "Armazenamento Interno"
                    # Não precisa de permissão especial de WRITE_EXTERNAL_STORAGE pra isso
                    file_path = activity.getExternalFilesDir(None).getAbsolutePath()
                    self.arquivo_gravado = os.path.join(file_path, 'tiro_temp.wav')
                else:
                    self.arquivo_gravado = "tiro_temp.wav"
                
                # Deleta se já existir para não bugar o header do wav
                if os.path.exists(self.arquivo_gravado):
                    os.remove(self.arquivo_gravado)

                audio.start(file_path=self.arquivo_gravado)
                # ... resto do código ...  

                audio.start(file_path=self.arquivo_gravado)
                self.gravando = True
                self.btn_gravar.text = "PARAR Gravação (Gravando...)"
                self.lbl_status.text = "Gravando... Dê o tiro!"
            except Exception as e:
                self.lbl_status.text = f"Erro ao gravar: {e}"
        else:
            # PARAR
            try:
                audio.stop()
                self.gravando = False
                self.btn_gravar.text = "GRAVAR Áudio (In App)"
                self.lbl_status.text = "Gravação finalizada. Analisando..."
                # Chama análise direto no arquivo gravado
                self.processar_analise(self.arquivo_gravado)
            except Exception as e:
                self.lbl_status.text = f"Erro ao parar: {e}"

    def escolher_arquivo(self, instance):
        if platform == 'android':
            from plyer import filechooser
            filechooser.open_file(on_selection=self.arquivo_selecionado)
        else:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                path = filedialog.askopenfilename()
                if path:
                    self.arquivo_selecionado([path])
            except:
                pass

    def arquivo_selecionado(self, selection):
        if selection:
            self.processar_analise(selection[0])

    def processar_analise(self, filename):
        # Validação Inputs
        try:
            d = float(self.input_dist.text)
            d_err = float(self.input_dist_err.text)
            t = float(self.input_temp.text)
            t_err = float(self.input_temp_err.text)
        except ValueError:
            self.lbl_status.text = "Erro: Verifique os números digitados."
            return

        self.lbl_status.text = f"Analisando..."
        
        try:
            # Chamada atualizada com incertezas
            res, img_path = analise_audio.analisar_audio(filename, d, d_err, t, t_err)
            
            if res:
                # Formata resultado bonito
                v = res['v_bala'] # é um ufloat
                self.lbl_status.text = (f"[b]Velocidade:[/b] {v.n:.1f} +/- {v.s:.1f} m/s\n"
                                        f"Delta T: {res['delta_t'].n*1000:.1f}ms")
                self.img_result.source = img_path
                self.img_result.reload()
            else:
                self.lbl_status.text = f"Falha: {img_path}"
        except Exception as e:
            self.lbl_status.text = f"Crash: {str(e)}"

if __name__ == '__main__':
    BalisticaApp().run()
