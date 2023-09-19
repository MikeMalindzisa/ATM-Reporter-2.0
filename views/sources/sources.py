import os
import re
import time

import openpyxl
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView

import app
from config import ConfigReader

Builder.load_file(app.resource_path('views/sources/sources.kv'))


def natural_key(path):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', path)]


def natural_sort(files, filesystem, directory):
    directory_files = [f for f in files if filesystem.is_dir(f) and os.path.dirname(f) == directory]
    xlsx_files = [f for f in directory_files if f.lower().endswith('.xlsx')]
    return sorted(xlsx_files, key=natural_key)


def open_spa_file(file_path):
    # Get the file size
    file_size = os.path.getsize(file_path)

    # Get the file creation date and format it
    file_date = os.path.getctime(file_path)
    formatted_date = time.strftime("%d %b %Y", time.localtime(file_date))

    return file_size, formatted_date


class SPAFileChooserList(BoxLayout):
    source_screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SPAFileChooserList, self).__init__(**kwargs)
        config_reader = ConfigReader()
        self.config = config_reader.get_sys_config()
        self.source_screen = self.source_screen
        self.orientation = 'vertical'
        self.fc = FileChooserListView()  # Create the custom file chooser
        self.fc.is_selectable = True  # Disable selecting directories
        self.fc.filters = ["*.spa"]  # Set filter to display only .xlsx files
        self.fc.rootpath = self.config.get("source_folder")
        filter_dirs: True
        self.fc.path = self.config.get("source_folder")
        self.fc.bind(selection=self.on_file_selected)
        self.add_widget(self.fc)

    def on_file_selected(self, instance, value):
        if value:
            selected_file = value[0]
            file_name = os.path.basename(selected_file)  # Extract file name
            self.file_details(file_name)
            self.source_screen.ids.download_source_file.disabled = False

    def file_details(self, file_name):
        file_path = os.path.join(self.config.get("source_folder"), file_name)
        file_size, formatted_date = open_spa_file(file_path)

        # Display file size in KB, MB, or GB
        if file_size < 1024:
            formatted_size = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            formatted_size = f"{file_size / 1024:.2f} KB"
        elif file_size < 1024 * 1024 * 1024:
            formatted_size = f"{file_size / (1024 * 1024):.2f} MB"
        else:
            formatted_size = f"{file_size / (1024 * 1024 * 1024):.2f} GB"

        # Update the labels with file details
        self.source_screen.ids.report_date.text = f"{formatted_date}"
        self.source_screen.ids.file_size.text = f"{formatted_size}"
        self.source_screen.ids.selected_report_name.text = f"{file_name}"
        self.source_screen.ids.reports_count.text = f"({1}) File Selected"


class SPAFileChooserIcon(BoxLayout):
    source_screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SPAFileChooserIcon, self).__init__(**kwargs)
        self.source_screen = self.source_screen

        config_reader = ConfigReader()
        self.config = config_reader.get_sys_config()

        self.fc = FileChooserIconView()  # Create the custom file chooser
        self.fc.is_selectable = True  # Disable selecting directories
        self.fc.filters = ["*.spa"]  # Set filter to display only .xlsx files
        self.fc.rootpath = self.config.get("source_folder")
        self.filter_dirs = True
        self.fc.path = self.config.get("source_folder")
        self.fc.bind(selection=self.on_file_selected)
        self.add_widget(self.fc)

    def on_file_selected(self, instance, value):
        if value:
            selected_file = value[0]
            file_name = os.path.basename(selected_file)  # Extract file name
            self.file_details(file_name)

            self.source_screen.ids.download_source_file.disabled = False

    def file_details(self, file_name):
        file_path = os.path.join(self.config.get("source_folder"), file_name)
        file_size, formatted_date = open_spa_file(file_path)

        # Display file size in KB, MB, or GB
        if file_size < 1024:
            formatted_size = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            formatted_size = f"{file_size / 1024:.2f} KB"
        elif file_size < 1024 * 1024 * 1024:
            formatted_size = f"{file_size / (1024 * 1024):.2f} MB"
        else:
            formatted_size = f"{file_size / (1024 * 1024 * 1024):.2f} GB"

        # Update the labels with file details
        self.source_screen.ids.report_date.text = f"{formatted_date}"
        self.source_screen.ids.file_size.text = f"{formatted_size}"
        self.source_screen.ids.selected_report_name.text = f"{file_name}"
        self.source_screen.ids.reports_count.text = f"({1}) File Selected"


class SourcesScreen(BoxLayout):
    source_screen = ObjectProperty(None)  # Declare the ObjectProperty

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        ObjectProperty(natural_sort)
