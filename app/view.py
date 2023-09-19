import os
import sys

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.properties import StringProperty
import datetime


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow(BoxLayout):
    logo = StringProperty(resource_path("assets/icons/logo.ico"))
    dateToday = datetime.datetime.now().strftime('%A, %d %B %Y')

    def __init__(self, **kw):
        super().__init__(**kw)


class NavTab(ToggleButtonBehavior, BoxLayout):
    text = StringProperty("")
    icon = StringProperty("")
    icon_active = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
