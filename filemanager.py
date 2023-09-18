from kivymd.app import MDApp

from kivymd_extensions.filemanager import FileManager


class MainApp(MDApp):
    def on_start(self):
        FileManager().open()


if __name__ == "__main__":
    MainApp().run()
