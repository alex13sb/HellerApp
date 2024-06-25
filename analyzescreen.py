from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import os
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from kivy.clock import Clock

class AnalyzeScreen(Screen):
    def __init__(self, **kwargs):
        super(AnalyzeScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(text='Loading predictions...')
        self.layout.add_widget(self.label)
        self.add_widget(self.layout)

    def set_images_dir(self, images_dir):
        self.images_dir = images_dir
        Clock.schedule_once(self._predict_images, 0)

    def _predict_images(self, dt):
        model = load_model('best_model.h5')
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

        self.label.text = f"Predictions:\n{result_text}"
