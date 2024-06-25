import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.label import Label
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
        spinner = Spinner(
            text='CNC Modell wählen',
            values=('PT16-M55013', 'PT16-M58038', 'Add Model'),
            size_hint=(None, None),
            size=(200, 44),
            pos_hint={'center_x': .5, 'center_y': .5})
        
        self.slider = Slider(min=1, max=60, value=30)
        slider_value = Label(text=f'Sekunden: {int(self.slider.value)}')
        self.slider.bind(value=lambda instance, value: setattr(slider_value, 'text', f'Sekunden: {int(value)}'))
        layout.add_widget(spinner)
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
        if self.filechooser.selection:
            selected_path = self.filechooser.selection[0]
            Logger.info(selected_path)
            self.load_wave_file(selected_path)

            file_name = os.path.basename(selected_path)
            recording_screen = self.manager.get_screen('recordingscreen')
            recording_screen.set_audio_data(self.audio_data, self.sample_rate, file_name, selected_path)
            
        self.manager.current = 'recordingscreen'

    def load_wave_file(self, file_path):
        try:
            self.audio_data, self.sample_rate = librosa.load(file_path, sr=None)
            
        except Exception as e:
            Logger.info('Error loading the file!')
