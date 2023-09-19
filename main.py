import os.path
import sys
from os.path import dirname, join

from kivy.resources import resource_add_path

from app import MainApp

if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS'):
        resource_add_path((os.path.join(sys._MEIPASS)))
    MainApp().run()
