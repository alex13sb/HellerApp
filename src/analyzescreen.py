from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from kivy.clock import Clock
from kivy.logger import Logger
import shutil

class AnalyzeScreen(Screen):
    def __init__(self, **kwargs):
        super(AnalyzeScreen, self).__init__(**kwargs)
        self.selected_model = '../models/pt16-m55013.h5'
        self.temp_dir = ""
        self.predicted_data = []  # Liste für bestätigte Vorhersagen

        self.layout = BoxLayout(orientation='vertical')
        self.button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)

        # Button at the bottom of the screen to start new analysis
        self.new_analysis_button = Button(
            text="Neue Analyse starten", size_hint=(1, 1), disabled=True
        )
        self.new_analysis_button.bind(on_press=self.go_to_main_screen)
        self.button_layout.add_widget(self.new_analysis_button)

        # Button to confirm correct prediction
        self.confirm_button = Button(
            text="Zum Modell hinzufügen",
            size_hint=(1, 1),
            disabled=True  # Starte deaktiviert, bis Vorhersagen geladen sind
        )
        self.confirm_button.bind(on_press=self.confirm_prediction)
        self.button_layout.add_widget(self.confirm_button)

        self.layout.add_widget(self.button_layout)
        self.add_widget(self.layout)  # Hinzufügen des Layouts zum Screen

    def set_images_dir(self, images_dir):
        self.images_dir = images_dir
        Clock.schedule_once(self._predict_images, 0)

    def _predict_images(self, dt):
        current_working_directory = os.getcwd()
        model_folder = os.path.join(current_working_directory, "models")
        model_name = os.path.join(model_folder, self.selected_model + ".h5")
        Logger.info(f"model_name is {model_name}")
        model = load_model(model_name)
        all_class_labels = {
            0: 'Aluminium - Materialfehler, ohne Werkzeugfehler',
            1: 'Aluminium - Materialfehler, Werkzeugfehler',
            2: 'Aluminium - ohne Materialfehler, ohne Werkzeugfehler',
            3: 'Aluminium - ohne Materialfehler, Werkzeugfehler',
            4: 'Kunststoff - Materialfehler, ohne Werkzeugfehler',
            5: 'Kunststoff - Materialfehler, Werkzeugfehler',
            6: 'Kunststoff - ohne Materialfehler, ohne Werkzeugfehler',
            7: 'Kunststoff - ohne Materialfehler, Werkzeugfehler'
        }

        result_data = []

        for img_file in os.listdir(self.images_dir):
            if img_file.endswith('.png'):
                img_path = os.path.join(self.images_dir, img_file)
                img = image.load_img(img_path, target_size=(256, 256))
                img_array = image.img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0) / 255.0

                prediction = model.predict(img_array)
                predicted_class = np.argmax(prediction, axis=1)
                predicted_label = all_class_labels[predicted_class[0]]

                # Extract Bahn number from filename
                bahn_number = int(img_file.split('.')[0])
                result_data.append((bahn_number, predicted_label, prediction[0]))

        # Sort by bahn_number
        result_data.sort(key=lambda x: x[0])

        self.layout.clear_widgets()  # Clear previous widgets

        for bahn_number, predicted_label, prediction_percentages in result_data:
            display_text = f"Bahn {bahn_number}: {predicted_label}"
            percentages_text = ", ".join([f"{label}: {percent:.2f}%" for label, percent in zip(all_class_labels.values(), prediction_percentages)])

            # Create a layout for each prediction
            prediction_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30,spacing=10)
            prediction_label = Label(text=display_text, halign='left', size_hint=(1, None), height=30)
            radio_button = ToggleButton(group='bahn', size_hint=(None, None), height=20, halign='left')
            
            prediction_layout.add_widget(prediction_label)
            prediction_layout.add_widget(radio_button)

            self.layout.add_widget(prediction_layout)
        
        # Add the button layout at the bottom again
        self.layout.add_widget(self.button_layout)

        self.new_analysis_button.disabled = False
        self.confirm_button.disabled = False



    def confirm_prediction(self, instance):
        confirmed_predictions = self.predicted_data[:]  # Kopie der bestätigten Vorhersagen
        Logger.info("User hat bestätigte Vorhersagen zum Modell hinzugefügt.")

        self.incremental_learning(confirmed_predictions)

    def incremental_learning(self, confirmed_predictions):
        # Beispiel für inkrementelles Lernen: Dummy-Funktion, die das Modell mit bestätigten Daten aktualisiert
        # Du musst diese Methode entsprechend deinem Modell und den bestätigten Daten implementieren
        Logger.info("Starte inkrementelles Lernen mit bestätigten Daten...")

        # Pseudo-Code: Du müsstest das Modell mit den neuen bestätigten Daten aktualisieren
        # Zum Beispiel: model.fit(new_data_x, new_data_y)

        # Speichern des aktualisierten Modells
        # Zum Beispiel: model.save('updated_model.h5')

    def go_to_main_screen(self, instance):
        # Hier kannst du die markierten Vorhersagen dem Modell hinzufügen oder speichern
        Logger.info("Vorhersagen verworfen")
        shutil.rmtree(self.temp_dir)
        self.manager.current = 'main'
