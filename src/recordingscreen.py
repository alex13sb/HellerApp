from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
import os
import tempfile
import sys
import librosa
import pandas as pd
from pydub import AudioSegment
from maad import sound, util
from maad.rois import template_matching
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.logger import Logger
import threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pywt

class RecordingScreen(Screen):
    def __init__(self, **kwargs):
        super(RecordingScreen, self).__init__(**kwargs)
        self.selected_seconds = 21  # Standardwert für Sekunden
        self.selected_model = 'pt16-m55013'  # Standardwert für Modell
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.file_name_label = Label(text="No file selected", size_hint=(1, None), height=40)
        self.layout.add_widget(self.file_name_label)

        self.progress = ProgressBar(max=100, value=0, size_hint=(1, None), height=20)
        self.layout.add_widget(self.progress)
        self.layout.add_widget(BoxLayout(size_hint=(1, 1)))
        self.analyse_button = Button(text="Bahnen analysieren", size_hint=(1, None), height=50, disabled=True)
        self.layout.add_widget(self.analyse_button)


        self.add_widget(self.layout)
        self.animating = True
        self._animate()

    def _animate(self):
        if self.animating:
            if self.progress.value >= 100:
                self.progress.value = 0
            else:
                self.progress.value += 1
            Clock.schedule_once(lambda dt: self._animate(), 0.1)

    def stop_animation(self):
        self.animating = False

    def set_audio_data(self, audio_data, sample_rate, file_name, recorded_path):
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.file_name_label.text = file_name
        self.audio_path = recorded_path

        # Prüfen, ob die App als .exe läuft
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.getcwd()

        session_folder = os.path.join(base_path, 'session_folder')
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        self.temp_dir = tempfile.mkdtemp(dir=session_folder)
        Logger.info(f'Temporary directory created at {self.temp_dir}')

        threading.Thread(target=self.process_audio_file, args=(recorded_path, self.temp_dir)).start()

    def show_error_popup(self, error_message):
        # Popup über Clock auf dem Hauptthread ausführen
        Clock.schedule_once(lambda dt: self._show_error_popup_on_main_thread(error_message))

    def _show_error_popup_on_main_thread(self, error_message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=error_message, halign='center'))
        
        return_button = Button(text='Zurück zur Startseite', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5})
        content.add_widget(return_button)

        popup = Popup(title='Fehler', content=content, size_hint=(None, None), size=(400, 200))

        # Button bindet zur Startseite zurück
        return_button.bind(on_press=lambda x: self.return_to_main(popup))

        popup.open()

    def return_to_main(self, popup):
        popup.dismiss()
        self.manager.current = 'main'


    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for development and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)


    def process_audio_file(self, input_file, output_folder):
        try:
            template_folder = self.resource_path("src/templates")
            template_name = os.path.join(template_folder, self.selected_model + ".wav")
            min_t_values = self.get_timestamps(input_file, template_name)
            Logger.info(min_t_values)
            if len(min_t_values) > 0:
                audio = AudioSegment.from_wav(input_file)
                for i, start_time in enumerate(min_t_values):
                    if i < len(min_t_values) - 1:
                        end_time = min_t_values[i + 1] * 1000
                    else:
                        end_time = len(audio)

                    start_time_ms = start_time * 1000
                    segment = audio[start_time_ms:end_time]

                    output_file_name = f"{os.path.splitext(os.path.basename(input_file))[0]}_segment_{i + 1}.wav"
                    output_path = os.path.join(output_folder, output_file_name)
                    segment.export(output_path, format="wav")
                    Logger.info(f"Segment {i + 1} done in {output_file_name}")
            else:
                Logger.info(f"No segments found in {input_file}!")
            threading.Thread(target=self.generate_images).start()

        except Exception as e:
            Logger.error(f"Error processing audio file: {e}")
            self.show_error_popup(f"Fehler beim Verarbeiten der Audiodatei: {e}")


    def delete_long_audio_files(self, directory):
        try:
            max_duration = self.selected_seconds + 2  # Puffer-Zeit 2 Sekunden
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if filepath.lower().endswith('.wav'):
                    try:
                        y, sr = librosa.load(filepath, sr=None)
                        duration = librosa.get_duration(y=y, sr=sr)
                        if duration > max_duration:
                            os.remove(filepath)
                            Logger.info(f"Deleted {filepath} - Duration: {duration} seconds")
                    except Exception as e:
                        Logger.error(f"Failed to process {filepath}: {e}")
        except Exception as e:
            Logger.error(f"Error deleting long audio files: {e}")
            self.show_error_popup(f"Fehler beim Löschen der langen Audiodateien: {e}")


    def generate_images(self):
        try:
            output_dir = self.temp_dir
            counter = 1
            for filename in os.listdir(output_dir):
                if filename.endswith('.wav'):
                    filepath = os.path.join(output_dir, filename)
                    self.save_spectrogram_as_image(filepath, output_dir, counter)
                    counter += 1
            Clock.schedule_once(self.enable_analyse_button, 0)
        except Exception as e:
            Logger.error(f"Error generating images: {e}")
            self.show_error_popup(f"Fehler beim Generieren der Bilder: {e}")

    def enable_analyse_button(self, dt):
        self.analyse_button.disabled = False
        self.progress.value = 100
        self.stop_animation()
        self.analyse_button.bind(on_press=lambda instance: self.go_to_analyze_screen(self.temp_dir))

    def go_to_analyze_screen(self, output_folder):
        analyze_screen = self.manager.get_screen('analyzescreen')
        analyze_screen.set_images_dir(output_folder)
        analyze_screen.selected_model = self.selected_model
        analyze_screen.temp_dir = self.temp_dir
        self.manager.current = 'analyzescreen'


    def save_melspectrogram_as_image(self, filename, output_dir, counter):
        y, sr = librosa.load(filename)
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=256, n_fft=2048, hop_length=512)
        
        # Umwandlung in dB-Skala
        S_db = librosa.amplitude_to_db(S, ref=np.max)
        
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(S_db, sr=sr, hop_length=512, x_axis=None, y_axis=None)  # Achsen entfernen
        plt.axis('off')  # Achsen deaktivieren
        plt.tight_layout(pad=0)  # Padding entfernen
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(os.path.join(output_dir, f'{counter}.png'))
        plt.close()



    def save_cwt_as_image(self, filename, output_dir, counter):
        y, sr = librosa.load(filename)
        wavelet = 'mexh'
        scales = np.arange(1, 32)
        
        # Durchführung der Continuous Wavelet Transform
        coefficients, _ = pywt.cwt(y, scales, wavelet, sampling_period=1/sr)
        
        # Erstellen des Skalogramms
        plt.figure(figsize=(12, 6))
        plt.imshow(np.abs(coefficients), extent=[0, len(y)/sr, scales.max(), scales.min()],
                cmap='coolwarm', aspect='auto', vmax=abs(coefficients).max()/2, vmin=abs(coefficients).min())
        plt.axis('off')  # Achsen deaktivieren
        plt.tight_layout(pad=0)  # Padding entfernen
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(os.path.join(output_dir, f'{counter}.png'))
        plt.close()



    def save_dwt_as_image(self, filename, output_dir, counter):
        y, sr = librosa.load(filename)
        wavelet = 'haar'
        
        # Durchführung der diskreten Wavelet-Transformation (DWT) für ein Level
        cA, cD = pywt.dwt(y, wavelet)
        
        # Berechnung der absoluten Koeffizientenwerte
        cA_abs = np.abs(cA)
        cD_abs = np.abs(cD)
        
        # Erstellen eines 2D-Arrays für die Darstellung
        coeffs_array = np.vstack([cD_abs, cA_abs])
        
        # Erstellen des Skalogramms
        plt.figure(figsize=(12, 6))
        plt.imshow(coeffs_array, aspect='auto', cmap='viridis', extent=[0, len(y)/sr, 0, 1], 
                vmax=abs(coeffs_array).max()/2, vmin=abs(coeffs_array).min())
        plt.axis('off')  # Achsen deaktivieren
        plt.tight_layout(pad=0)  # Padding entfernen
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(os.path.join(output_dir, f'{counter}.png'))
        plt.close()
    


    def save_spectrogram_as_image(self, filename, output_dir, counter):
        y, sr = librosa.load(filename)
        S = np.abs(librosa.stft(y, hop_length=512))
        S_db = librosa.amplitude_to_db(S, ref=np.max)
        
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(S_db, sr=sr, hop_length=512, x_axis=None, y_axis=None)  # Achsen entfernen
        plt.axis('off')  # Achsen deaktivieren
        plt.tight_layout(pad=0)  # Padding entfernen
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(os.path.join(output_dir, f'{counter}.png'))
        plt.close()



    def on_leave(self, *args):
        self.analyse_button.disabled = True
        self.animating = True
        self._animate()


    def aggregate(self, rois_df):
        if rois_df.empty:
            Logger.error("Empty DataFrame in aggregate function. No data to process.")
            return pd.DataFrame()  # Leerer DataFrame zurückgeben
        
        window = self.selected_seconds
        aggregated = []
        current_group = rois_df.iloc[0].copy()
        for index, row in rois_df.iterrows():
            if row['peak_time'] <= current_group['peak_time'] + window:
                current_group['xcorrcoef'] = max(current_group['xcorrcoef'], row['xcorrcoef'])
                current_group['max_t'] = max(current_group['max_t'], row['max_t'])
            else:
                aggregated.append(current_group)
                current_group = row.copy()
        aggregated.append(current_group)
        return pd.DataFrame(aggregated)

    

    def get_timestamps(self, signal_name, template_name, offset=0):
        flims = (6000, 12000)
        db_range = 80
        template, fs_template = librosa.load(template_name, sr=None)
        audio, fs_audio = librosa.load(signal_name, sr=None)
        Sxx_template, _, _, _ = sound.spectrogram(template, fs_template)
        Sxx_template = util.power2dB(Sxx_template, db_range)
        Sxx_audio, tn, fn, ext = sound.spectrogram(audio, fs_audio)
        Sxx_audio = util.power2dB(Sxx_audio, db_range)
        peak_th = 0.75
        xcorrcoef, rois = template_matching(Sxx_audio, Sxx_template, tn, ext, peak_th)
        rois['min_f'] = flims[0]
        rois['max_f'] = flims[1]
        rois_df = pd.DataFrame(rois)
        Logger.info(rois_df)
        if rois_df.empty:  # Hier überprüfen wir, ob der DataFrame leer ist.
            Logger.error("No ROIs found in get_timestamps.")
            self.show_error_popup("Keine Segmente gefunden! Bitte prüfen Sie die Audiodatei.")
            return []

        aggregated_rois = self.aggregate(rois_df)
        min_t_values = aggregated_rois['min_t'].values + offset
        return min_t_values




