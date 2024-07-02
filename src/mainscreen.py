from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        btn = Button(text="Analyse starten")
        btn.bind(on_release=self.change_screen)
        self.add_widget(btn)

    def change_screen(self, *args):
        self.manager.current = 'options'

