from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
import os
import tempfile

import librosa
import pandas as pd
from pydub import AudioSegment
from maad import sound, util
from maad.rois import template_matching
from kivy.uix.button import Button

from kivy.logger import Logger
import threading
from matplotlib import pyplot as plt
import numpy as np


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

        self.analyse_button = Button(text="Analyse starten", size_hint=(1, None), height=50, disabled=True)
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

        session_folder = os.path.join(os.getcwd(), 'session_folder')
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        self.temp_dir = tempfile.mkdtemp(dir=session_folder)
        Logger.info(f'Temporary directory created at {self.temp_dir}')

        threading.Thread(target=self.process_audio_file, args=(recorded_path, self.temp_dir)).start()

    def process_audio_file(self, input_file, output_folder):
        template_name = self.selected_model + ".wav" # BigBen Sound 
        min_t_values = self.get_timestamps(input_file, template_name)
        
        if len(min_t_values) > 0:
            audio = AudioSegment.from_wav(input_file)
            for i, start_time in enumerate(min_t_values):
                if i < len(min_t_values) - 1:
                    end_time = min_t_values[i+1] * 1000
                else:
                    end_time = len(audio)
                
                start_time_ms = start_time * 1000
                segment = audio[start_time_ms:end_time]
                
                output_file_name = f"{os.path.splitext(os.path.basename(input_file))[0]}_segment_{i+1}.wav"
                output_path = os.path.join(output_folder, output_file_name)
                segment.export(output_path, format="wav")
                Logger.info(f"Segment {i+1} done in {output_file_name}")
        else:
            Logger.info(f"No segments found in {input_file}!")

        self.delete_long_audio_files(output_folder)
        threading.Thread(target=self.generate_images).start()


    def delete_long_audio_files(self, directory):
        max_duration = self.selected_seconds + 2 # Puffer-Zeit 2 Sekunden
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if filepath.lower().endswith(('.wav')):
                try:
                    y, sr = librosa.load(filepath, sr=None)
                    duration = librosa.get_duration(y=y, sr=sr)
                    
                    if duration > max_duration:
                        os.remove(filepath)
                        Logger.info(f"Deleted {filepath} - Duration: {duration} seconds")
                except Exception as e:
                    Logger.error(f"Failed to process {filepath}: {e}")


    def generate_images(self):
        output_dir = self.temp_dir
        counter = 1
        bahn = "Bahn_"
        for filename in os.listdir(output_dir):
            if filename.endswith('.wav'):
                filepath = os.path.join(output_dir, filename)
                self.save_spectrogram_as_image(filepath, output_dir, bahn+str(counter))
                counter += 1
        Clock.schedule_once(self.enable_analyse_button, 0)

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
        aggregated_rois = self.aggregate(rois_df)
        min_t_values = aggregated_rois['min_t'].values + offset
        if len(min_t_values) > 1:
            min_t_values = min_t_values[:-1]
        else:
            min_t_values = []
        return min_t_values




