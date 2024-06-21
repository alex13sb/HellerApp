from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Rotate
from kivy.uix.progressbar import ProgressBar

class RecordingScreen(Screen):
    def __init__(self, **kwargs):
        super(RecordingScreen, self).__init__(**kwargs)
        self.progress = ProgressBar(max=100, value=0, size_hint=(None, None), size=(200, 20), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.progress)
        self._animate()

    def _animate(self):
        if self.progress.value >= 100:
            self.progress.value = 0
        else:
            self.progress.value += 1
        Clock.schedule_once(lambda dt: self._animate(), 0.1)
