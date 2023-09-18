import datetime
import os
import xml.etree.ElementTree as eT

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import rgba
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel

from app import MainApp
from config import ConfigReader

Builder.load_file('views/settings/settings.kv')


def toggle_checkbox(checkbox):
    checkbox.active = not checkbox.active


class CustomLabel(MDLabel):
    pass


class SettingsScreen(BoxLayout):
    # Define other input fields here...
    dialog = None

    def __init__(self, **kw) -> None:
        super().__init__(**kw)

        self.config_reader = ConfigReader()
        self.config = self.config_reader.get_sys_config()

        Clock.schedule_once(self.render, 10.0)
        Clock.schedule_once(self.update_state, 10.0)

    def render(self, _):
        self.ids.db_host.text = self.config.get("database_host")
        self.ids.db_port.text = self.config.get("database_port")
        self.ids.db_name.text = self.config.get("database_name")
        self.ids.db_user.text = self.config.get("database_user")
        self.ids.db_pass.text = "" if self.config.get("database_password") is None \
            else self.config.get("database_password")
        self.ids.source_folder.text = self.config.get("source_folder")
        self.ids.archive_folder.text = self.config.get("archive_folder")
        self.ids.reports_folder.text = self.config.get("reports_folder")

        if self.config.get("configuration_type") == "default":
            self.ids.default_config.active = True

    def update_state(self, _):
        config_reader = ConfigReader()
        if config_reader.get_state():
            self.ids.watchdog_service_start.disabled = True
            self.ids.watchdog_service_stop.disabled = False
            self.ids.watchdog_service_status.text = "(Online)"
            self.ids.watchdog_service_status.theme_text_color = "Primary"
        else:
            self.ids.watchdog_service_start.disabled = False
            self.ids.watchdog_service_stop.disabled = True
            self.ids.watchdog_service_status.text = "(Offline)"
            self.ids.watchdog_service_status.theme_text_color = "Error"

    def show_message_popup_d(self, message):
        if not self.dialog:
            self.dialog = MDDialog(
                title="STD ATM - Settings",
                text=message,
                buttons=[
                    MDRaisedButton(
                        text="Ok", on_release=self.close_dialog
                    ),
                ],
            )
        self.dialog.open()

    def show_message_popup(self, message):
        if not self.dialog:
            self.dialog = MDDialog(
                title="STD ATM - Settings",
                text=message,
                buttons=[
                    MDRaisedButton(
                        text="Ok", on_release=self.close_dialog
                    ),
                ],
                auto_dismiss=False
            )
        else:
            self.dialog.text = message
        self.dialog.open()

    def show_message_popup_restart(self, message):
        if not self.dialog:
            self.dialog = MDDialog(
                title="STD ATM - Settings",
                text=message,
                buttons=[
                    MDRaisedButton(
                        text="Restart Now", on_release=self.restart
                    ),
                ],
                auto_dismiss=False
            )
        else:
            self.dialog.text = message
        self.dialog.open()

    # Click Cancel Button
    def close_dialog(self, obj):
        self.dialog.dismiss(force=True)

    def test_database_connection(self):
        res = self.config_reader.test_database_connection()
        self.show_message_popup(res)

    def toggle_default_config(self, active):
        if active:
            self.ids.db_host.text = "localhost"
            self.ids.db_port.text = "3306"
            self.ids.db_name.text = "atm_data"
            self.ids.db_user.text = "root"
            self.ids.db_pass.text = ""
            self.ids.source_folder.text = "sources"
            self.ids.archive_folder.text = "completed"
            self.ids.reports_folder.text = "reports"

            os.makedirs(self.ids.source_folder.text, exist_ok=True)
            os.makedirs(self.ids.reports_folder.text, exist_ok=True)
            os.makedirs(self.ids.archive_folder.text, exist_ok=True)

    def save_configuration(self):
        root_element = eT.Element("configurations")

        config_type = "default" if self.ids.default_config.active else "custom"
        root_element.set("configuration_type", config_type)

        # Add the current date as an element
        current_date = eT.SubElement(root_element, "date")
        current_date.text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Database Configuration
        db_config = eT.SubElement(root_element, "database_configuration")
        eT.SubElement(db_config, "host").text = self.ids.db_host.text
        eT.SubElement(db_config, "port").text = self.ids.db_port.text
        eT.SubElement(db_config, "name").text = self.ids.db_name.text
        eT.SubElement(db_config, "user").text = self.ids.db_user.text
        eT.SubElement(db_config, "password").text = self.ids.db_pass.text

        # Working Directories
        working_dirs = eT.SubElement(root_element, "working_directories")
        eT.SubElement(working_dirs, "source_folder").text = self.ids.source_folder.text
        eT.SubElement(working_dirs, "reports_folder").text = self.ids.reports_folder.text
        eT.SubElement(working_dirs, "archive_folder").text = self.ids.archive_folder.text
        os.makedirs(self.ids.source_folder.text, exist_ok=True)
        os.makedirs(self.ids.reports_folder.text, exist_ok=True)
        os.makedirs(self.ids.archive_folder.text, exist_ok=True)
        tree = eT.ElementTree(root_element)
        tree.write("config.xml", encoding="utf-8", xml_declaration=True)
        self.show_message_popup_restart(f"Configuration saved successfully.\nApplication restart is required"
                                        f" to apply new system settings.")

    def start_watchdog_service(self):
        config_reader = ConfigReader()
        config_reader.start_observer()
        self.update_state(.1)

    def stop_watchdog_service(self):
        config_reader = ConfigReader()
        config_reader.stop_observer()
        self.update_state(.1)

    def restart(self, _):
        # Close the current instance of the app
        self.stop()
        # Launch a new instance of the app
        MainApp().run()
