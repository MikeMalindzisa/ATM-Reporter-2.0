from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.properties import StringProperty
import datetime


class MainWindow(BoxLayout):
    avatar = StringProperty("assets/imgs/avatar.jpg")
    logo = StringProperty("assets/icons/logo.ico")
    dateToday = datetime.datetime.now().strftime('%A, %d %B %Y')

    def __init__(self, **kw):
        super().__init__(**kw)


class NavTab(ToggleButtonBehavior, BoxLayout):
    text = StringProperty("")
    icon = StringProperty("")
    icon_active = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
