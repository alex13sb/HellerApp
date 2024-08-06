import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import platform
from kivy.logger import Logger
import librosa

class OptionsScreen(Screen):
    def __init__(self, **kwargs):
        super(OptionsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        file_method_label = Label(text="Analyse-Methode", size_hint_y=None, height=30)
        toggle_layout = BoxLayout(size_hint_y=None, height=50)
        btn_live = ToggleButton(text='Live', group='mode', state='down')
        btn_upload = ToggleButton(text='Upload', group='mode')
        btn_live.bind(on_press=self.on_toggle)
        btn_upload.bind(on_press=self.on_toggle)
        toggle_layout.add_widget(btn_live)
        toggle_layout.add_widget(btn_upload)

        # Caption for model selection
        model_selection_label = Label(text="Modellauswahl:", size_hint_y=None, height=30)
        
        self.spinner = Spinner(
            text='CNC Modell wählen',
            values=self.get_model_names(),
            size_hint=(None, None),
            size=(200, 44),
            pos_hint={'center_x': .5, 'center_y': .5})
        self.spinner.bind(text=self.on_spinner_select)

        # Layout for managing models
        model_manage_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
        model_manage_label = Label(text="Modelle verwalten:", size_hint_y=None, height=30, pos_hint={'center_x': 0.5})
        add_delete_layout = BoxLayout(size_hint=(None, None), size=(400, 50), pos_hint={'center_x': 0.5})

        add_model_button = Button(text="Modell hinzufügen", size_hint=(None, None), size=(200, 44))
        add_model_button.bind(on_press=self.add_model)
        self.delete_model_button = Button(text="Modell löschen", size_hint=(None, None), size=(200, 44), disabled=True)
        self.delete_model_button.bind(on_press=self.delete_model)
        add_delete_layout.add_widget(add_model_button)
        add_delete_layout.add_widget(self.delete_model_button)

        model_manage_layout.add_widget(model_manage_label)
        model_manage_layout.add_widget(add_delete_layout)
        layout.add_widget(model_manage_layout)

        self.seconds_input = TextInput(text='30', multiline=False, input_filter='int', size=(200, 50), halign="center")
        seconds_label = Label(text="Fräsbahnzeit in Sekunden (inklusive Start-Melodie):", size_hint_y=None, height=30)
        increase_button = Button(text='+', size_hint=(None, None), size=(44, 50), on_press=lambda instance: self.update_seconds(1))
        decrease_button = Button(text='-', size_hint=(None, None), size=(44, 50), on_press=lambda instance: self.update_seconds(-1))
        seconds_box = BoxLayout(size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5})
        seconds_box.add_widget(decrease_button)
        seconds_box.add_widget(self.seconds_input)
        seconds_box.add_widget(increase_button)
        layout.add_widget(model_selection_label)
        layout.add_widget(self.spinner)
        layout.add_widget(seconds_label)
        layout.add_widget(seconds_box)
        layout.add_widget(file_method_label)
        layout.add_widget(toggle_layout)

        documents_path = self.detect_documents_folder()
        #documents_path = r"C:\Users\alescha\OneDrive - Software AG\Desktop\HellerApp\"
        self.filechooser = FileChooserListView(path=documents_path, size_hint=(1, 1), opacity=0)
        self.filechooser.filters = ['*.wav', '!pagefile.sys', '!swapfile.sys', '!hiberfil.sys', '!*.tmp']
        layout.add_widget(self.filechooser)

        go_button = Button(text='GO', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        go_button.bind(on_press=self.go_pressed)
        layout.add_widget(go_button)

        self.add_widget(layout)

    def get_model_names(self):
        model_folder = os.path.join(os.getcwd(), "models")
        model_files = [f[:-3] for f in os.listdir(model_folder) if f.endswith('.h5')]
        return model_files

    def update_seconds(self, increment):
        current_value = int(self.seconds_input.text)
        new_value = max(0, current_value + increment)  # Prevent negative values
        self.seconds_input.text = str(new_value)

    def on_toggle(self, instance):
        if instance.text == 'Upload' and instance.state == 'down':
            self.show_filechooser_popup()
        else:
            self.filechooser.opacity = 0

    def show_filechooser_popup(self):
        filechooser_popup = FileChooserListView(filters=['*.wav'])
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(filechooser_popup)
        select_button = Button(text="Select", size_hint_y=None, height=50)
        popup_layout.add_widget(select_button)

        popup = Popup(title="Datei auswählen", content=popup_layout, size_hint=(0.9, 0.9))
        select_button.bind(on_press=lambda x: self.load_wave_file_from_chooser(filechooser_popup, popup))
        popup.open()

    def load_wave_file_from_chooser(self, filechooser, popup):
        if filechooser.selection:
            self.selected_path = filechooser.selection[0]
            Logger.info(self.selected_path)
            popup.dismiss()

    def go_pressed(self, instance):
        current_working_directory = os.getcwd()
        model_folder = os.path.join(current_working_directory, "models")
        selected_model_file = os.path.join(model_folder, self.spinner.text + ".h5")
        Logger.info(f"selected model_file is {selected_model_file}")
        
        if not os.path.exists(selected_model_file):
            self.show_model_not_found_popup()
            return

        if hasattr(self, 'selected_path') and self.selected_path:
            selected_path = self.selected_path
            Logger.info(selected_path)
            self.load_wave_file(selected_path)
            file_name = os.path.basename(selected_path)
            recording_screen = self.manager.get_screen('recordingscreen')
            recording_screen.set_audio_data(self.audio_data, self.sample_rate, file_name, selected_path)
            recording_screen.selected_seconds = int(self.seconds_input.text)
            recording_screen.selected_model = self.spinner.text
            self.manager.current = 'recordingscreen'
        else:
            self.no_file_selected_popup()


    def detect_documents_folder(self):
        documents_path = ""
        if platform.system() == 'Windows':
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
        elif platform.system() == 'Darwin':  # macOS
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
        elif platform.system() == 'Linux':
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
        elif platform.system() == 'Android':
            documents_path = '/storage/emulated/0/Documents'
        else:
            documents_path = os.path.expanduser('~')
        return documents_path

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

    def add_model(self, instance):
        filechooser_popup = FileChooserListView(filters=['*.h5'])
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(filechooser_popup)
        select_button = Button(text="Select", size_hint_y=None, height=50)
        popup_layout.add_widget(select_button)

        popup = Popup(title="Modell hinzufügen", content=popup_layout, size_hint=(0.9, 0.9))
        select_button.bind(on_press=lambda x: self.load_model(filechooser_popup, popup))
        popup.open()

    def on_spinner_select(self, spinner, text):
        if text and text != 'CNC Modell wählen':
            self.delete_model_button.disabled = False
        else:
            self.delete_model_button.disabled = True

    def delete_model(self, instance):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="Wirklich Modell löschen?", halign='center'))
        
        buttons_layout = BoxLayout(size_hint_y=None, height=50)
        yes_button = Button(text='Ja', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        no_button = Button(text='Nein', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        
        buttons_layout.add_widget(yes_button)
        buttons_layout.add_widget(no_button)
        
        content.add_widget(buttons_layout)
        
        popup = Popup(title='Bestätigung', content=content, size_hint=(None, None), size=(300, 200))
        
        yes_button.bind(on_press=lambda x: self.confirm_delete_model(popup))
        no_button.bind(on_press=popup.dismiss)
        
        popup.open()

    def confirm_delete_model(self, popup):
        model_folder = os.path.join(os.getcwd(), "models")
        selected_model_file = os.path.join(model_folder, self.spinner.text + ".h5")
        try:
            os.remove(selected_model_file)
            Logger.info(f"Deleted model file: {selected_model_file}")
            self.spinner.values = self.get_model_names()
            self.spinner.text = 'CNC Modell wählen'
            popup.dismiss()
        except Exception as e:
            Logger.error(f"Error deleting model file: {e}")
            self.show_error_popup(f"Fehler beim Löschen des Modells: {e}")

    def show_error_popup(self, error_message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=error_message, halign='center'))
        dismiss_button = Button(text='OK', size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5})
        content.add_widget(dismiss_button)

        popup = Popup(title='Fehler', content=content, size_hint=(None, None), size=(300, 200))
        dismiss_button.bind(on_press=popup.dismiss)
        popup.open()
