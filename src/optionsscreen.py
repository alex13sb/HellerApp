import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import librosa
from kivy.logger import Logger




class OptionsScreen(Screen):
    def __init__(self, **kwargs):
        super(OptionsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')


        toggle_layout = BoxLayout(size_hint_y=None, height=50)
        btn_live = ToggleButton(text='Live', group='mode', state='down')
        btn_upload = ToggleButton(text='Upload', group='mode')
        btn_live.bind(on_press=self.on_toggle)
        btn_upload.bind(on_press=self.on_toggle)

        toggle_layout.add_widget(btn_live)
        toggle_layout.add_widget(btn_upload)
        self.spinner = Spinner(
            text='CNC Modell wählen',
            values=('pt16-m55013', 'pt16-m58038'),
            size_hint=(None, None),
            size=(200, 44),
            pos_hint={'center_x': .5, 'center_y': .5})
        
        self.slider = Slider(min=1, max=60, value=30)
        slider_value = Label(text=f'Fräsbahnzeit in Sekunden (inklusive Start-Melodie): {int(self.slider.value)}')
        self.slider.bind(value=lambda instance, 
                         value: setattr(slider_value, 'text', f'Fräsbahnzeit in Sekunden (inklusive Start-Melodie): {int(value)}'))
        layout.add_widget(self.spinner)
        layout.add_widget(slider_value)
        layout.add_widget(self.slider)
        layout.add_widget(toggle_layout)


        self.filechooser = FileChooserListView(size_hint=(1, 1), opacity=0)
        self.filechooser.filters = ['*.wav', '!pagefile.sys', '!swapfile.sys', '!hiberfil.sys', '!*.tmp']
        layout.add_widget(self.filechooser)

        go_button = Button(text='GO', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        go_button.bind(on_press=self.go_pressed)
        layout.add_widget(go_button)

        self.add_widget(layout)

    def on_toggle(self, instance):
        if instance.text == 'Upload' and instance.state == 'down':
            self.filechooser.opacity = 1
        else:
            self.filechooser.opacity = 0

    def go_pressed(self, instance):
        current_working_directory = os.getcwd()
        model_folder = os.path.join(current_working_directory, "models")
        selected_model_file = os.path.join(model_folder, self.spinner.text + ".h5")
        Logger.info(f"selected model_file is {selected_model_file}")
        if not os.path.exists(selected_model_file):
            self.show_model_not_found_popup()
            return
        # falls modell vorhanden und file ausgewählt wurde
        if self.filechooser.selection:
            selected_path = self.filechooser.selection[0]
            Logger.info(selected_path)
            self.load_wave_file(selected_path)
            file_name = os.path.basename(selected_path)
            recording_screen = self.manager.get_screen('recordingscreen')
            recording_screen.set_audio_data(self.audio_data, self.sample_rate, file_name, selected_path)
            recording_screen.selected_seconds = int(self.slider.value)
            recording_screen.selected_model = self.spinner.text
            self.manager.current = 'recordingscreen'
        else: 
            self.no_file_selected_popup()


    def show_model_not_found_popup(self):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="Das ausgewählte Modell ist nicht vorhanden.", halign='center'))
        dismiss_button = Button(text='OK', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        content.add_widget(dismiss_button)
        
        popup = Popup(title='Modell nicht gefunden', content=content, size_hint=(None, None), size=(300, 200))
        dismiss_button.bind(on_press=popup.dismiss)
        popup.open()

    def no_file_selected_popup(self):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="Es wurde keine Datei ausgewählt.", halign='center'))
        dismiss_button = Button(text='OK', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        content.add_widget(dismiss_button)
        
        popup = Popup(title='Kein File gefunden', content=content, size_hint=(None, None), size=(300, 200))
        dismiss_button.bind(on_press=popup.dismiss)
        popup.open()

    def load_wave_file(self, file_path):
        try:
            self.audio_data, self.sample_rate = librosa.load(file_path, sr=None)
            
        except Exception as e:
            Logger.info('Error loading the file!')
