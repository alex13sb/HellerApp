from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from mainscreen import MainScreen
from optionsscreen import OptionsScreen
from recordingscreen import RecordingScreen
class HellerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(RecordingScreen(name='recording_screen'))
        return sm

if __name__ == "__main__":
    HellerApp().run()
