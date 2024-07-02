from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from mainscreen import MainScreen
from optionsscreen import OptionsScreen
from recordingscreen import RecordingScreen
from analyzescreen import AnalyzeScreen
import shutil
import os
from kivy.logger import Logger
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
class HellerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(RecordingScreen(name='recordingscreen'))
        analyze_screen = AnalyzeScreen(name='analyzescreen')
        sm.add_widget(analyze_screen)
        return sm
    
    def on_stop(self):
        current_working_directory = os.getcwd()
        session_folder = os.path.join(current_working_directory, "session_folder")
        # Überprüfen, ob der Ordner existiert
        if os.path.exists(session_folder):
            Logger.info("Deleting session_folder")
            # Ordner und dessen Inhalt löschen
            shutil.rmtree(session_folder)
        return super().on_stop()
if __name__ == "__main__":
    HellerApp().run()
