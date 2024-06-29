from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import os
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from kivy.clock import Clock
from kivy.logger import Logger
import shutil

class AnalyzeScreen(Screen):
    def __init__(self, **kwargs):
        super(AnalyzeScreen, self).__init__(**kwargs)
        self.selected_model = 'pt16-m55013.h5'
        self.temp_dir = ""
        self.predicted_data = []  # Liste für bestätigte Vorhersagen

        self.layout = BoxLayout(orientation='vertical')
        
        # Placeholder label for predictions
        self.predictions_label = Label(text='Loading predictions...', halign='center')
        self.layout.add_widget(self.predictions_label)
        
        # Spacer widget to push predictions label to the top
        self.layout.add_widget(BoxLayout(size_hint_y=None, height=1))
        
        # Button at the bottom of the screen to start new analysis
        self.new_analysis_button = Button(
            text="Neue Analyse starten", size_hint=(1, None), height=50, disabled=True
        )
        self.new_analysis_button.bind(on_press=self.go_to_options_screen)
        self.layout.add_widget(self.new_analysis_button)
        
        # Button to confirm correct prediction
        self.confirm_button = Button(
            text="Zum Modell hinzufügen",
            size_hint=(1, None),
            height=50,
            disabled=True  # Starte deaktiviert, bis Vorhersagen geladen sind
        )
        self.confirm_button.bind(on_press=self.confirm_prediction)
        self.layout.add_widget(self.confirm_button)
        
        self.add_widget(self.layout)

    def set_images_dir(self, images_dir):
        self.images_dir = images_dir
        Clock.schedule_once(self._predict_images, 0)

    def _predict_images(self, dt):
        model_name = self.selected_model + ".h5"
        Logger.info(f"model_name is {model_name}")
        model = load_model(model_name)
        all_class_labels = ['alu_nut', 'alu_ohne', 'kunststoff_nut', 'kunststoff_ohne', 'kunststoff_nut_NiO', 'kunststoff_ohne_NiO']
        
        result_text = ""

        for img_file in os.listdir(self.images_dir):
            if img_file.endswith('.png'):
                img_path = os.path.join(self.images_dir, img_file)
                img = image.load_img(img_path, target_size=(256, 256))
                img_array = image.img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0) / 255.0

                prediction = model.predict(img_array)
                predicted_class = np.argmax(prediction, axis=1)
                predicted_label = all_class_labels[predicted_class[0]]
                
                result_text += f"{img_file}: {predicted_label}\n"
                self.predicted_data.append((img_file, predicted_label))


        self.predictions_label.text = f"Predictions:\n{result_text}"
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

    def go_to_options_screen(self, instance):
        # Hier kannst du die markierten Vorhersagen dem Modell hinzufügen oder speichern
        Logger.info("Markierte Vorhersagen werden dem Modell hinzugefügt oder gespeichert.")
        shutil.rmtree(self.temp_dir)
        self.manager.current = 'main'
