import os
import shutil
import subprocess

import pymysql
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import rgba
from kivymd.material_resources import dp
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDFillRoundFlatIconButton, MDRoundFlatButton
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.spinner import MDSpinner
from openpyxl.workbook import Workbook

from config import ConfigReader

Builder.load_file('views/rfilter/rfilter.kv')

report_data = None


class DataTableLayout(BoxLayout):
    rfilter_screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(DataTableLayout, self).__init__(**kwargs)
        self.rfilter_screen = self.rfilter_screen
        config_reader = ConfigReader()
        self.config = config_reader.get_sys_config()
        self.progress_dialog = MDDialog(
            title="Fetching report data...",
            size_hint=(None, None),
            size=("200dp", "120dp"),
            auto_dismiss=False,
        )
        self.progress_spinner = MDSpinner(size=("48dp", "48dp"))
        self.progress_spinner.size_hint = (None, None)
        self.progress_dialog.add_widget(self.progress_spinner)
        self.dt = MDDataTable(
            use_pagination=True,
            elevation=0,
            shadow_radius=0,
            rows_num=50,
            pagination_menu_pos='auto',
            background_color_header="#00286D",
            background_color_selected_cell="83ABF1",

            column_data=[
                ("[color=#FFFFFF]ATM ID[/color]", dp(30)),
                ("[color=#FFFFFF]Connection (Fibre/LTE)[/color]", dp(30)),
                ("[color=#FFFFFF]Uptime %[/color]", dp(30)),
                ("[color=#FFFFFF]Downtime %[/color]", dp(40)),
                ("[color=#FFFFFF]Total Downtime (HH:MM.SS)[/color]", dp(70)),
                ("[color=#FFFFFF]Downtime Info", dp(100)),
                ("[color=#FFFFFF]Report Date", dp(100)),
            ],
        )  # Create the custom datatable

        self.add_widget(self.dt)

    def filter_data(self):
        # Database connection parameters

        self.progress_dialog.open()

        def execute_query(dt):
            global report_data

            host = self.config.get("database_host")
            user = self.config.get("database_user")
            port = self.config.get("database_port")
            password = "" if self.config.get("database_password") is None \
                else self.config.get("database_password")
            db_name = self.config.get("database_name")
            try:
                connection = pymysql.connect(host=host, port=port, user=user, password=password, db=db_name)
                cursor = connection.cursor()
                if (
                        self.rfilter_screen.ids.start_date.text != "Select Start Date" and
                        self.rfilter_screen.ids.end_date.text != "Select End Date"
                ):
                    query = "SELECT atm_id, atm_connection, uptime_percent, t_downtime_percent, total_downtime, " \
                            "downtime_info, date_since " \
                            "FROM atm_detailed_data WHERE date_since BETWEEN '" + self.rfilter_screen.ids.start_date.text \
                            + "' AND '" + self.rfilter_screen.ids.end_date.text + "';"
                    print(query)
                    cursor.execute(query)

                if (
                        self.rfilter_screen.ids.start_date.text != "Select Start Date" and
                        self.rfilter_screen.ids.end_date.text == "Select End Date"
                ):
                    query = "SELECT atm_id, atm_connection, uptime_percent, t_downtime_percent, total_downtime, " \
                            "downtime_info, date_since FROM " \
                            "atm_detailed_data WHERE date_since BETWEEN '" + self.rfilter_screen.ids.start_date.text + \
                            "' AND '" + self.rfilter_screen.ids.start_date.text + "';"
                    cursor.execute(query)
                if (
                        self.rfilter_screen.ids.start_date.text == "Select Start Date" and
                        self.rfilter_screen.ids.end_date.text != "Select End Date"
                ):
                    query = "SELECT atm_id, atm_connection, uptime_percent, t_downtime_percent, total_downtime, " \
                            "downtime_info, date_since FROM " \
                            "atm_detailed_data WHERE date_since BETWEEN '" + self.rfilter_screen.ids.end_date.text + \
                            "' AND '" + self.rfilter_screen.ids.end_date.text + "';"
                    print(query)
                    cursor.execute(query)
                if (
                        self.rfilter_screen.ids.start_date.text == "Select Start Date" and
                        self.rfilter_screen.ids.end_date.text == "Select End Date"
                ):
                    self.show_popup("Select at least one date input to generate report.")

                if cursor.rowcount is 0:
                    self.show_popup("No data found for the filter parameters provided.")

                report_data = cursor.fetchall()

                headers = [col[0] for col in cursor.description]

                modified_row_data = []
                self.progress_dialog.title = "Preparing report data..."
                for row in report_data:
                    modified_row = ["ATM " + str(row[0])] + [str(item) for item in row[1:]]
                    modified_row_data.append(modified_row)
                self.progress_dialog.title = "Populating report table..."
                self.dt.column_data = [(header, dp(40)) for header in headers]
                if len(modified_row_data) > 0:
                    self.rfilter_screen.ids.export_xlsx_btn.disabled = False
                    self.dt.row_data = modified_row_data
                Clock.schedule_once(self.dismiss_progress_dialog, 1.5)
                connection.close()

            except pymysql.connect.Error as err:
                print("Error: {}".format(err))
        Clock.schedule_once(execute_query, 0.9)

    def dismiss_progress_dialog(self, dt):
        # Dismiss the progress dialog
        self.progress_dialog.dismiss()

    @staticmethod
    def show_popup(message):
        # Create an instance of MDDialog
        dialog = MDDialog(
            title="ATM Reporter",
            text=message,
            buttons=[
                MDFlatButton(
                    text="Close",  # Button text
                    on_release=lambda *args: dialog.dismiss()
                )
            ],
            auto_dismiss=False
        )

        # Display the dialog
        dialog.open()


class RFilterScreen(BoxLayout):
    rfilter_screen = ObjectProperty(None)
    dialog = None
    progress_bar = MDProgressBar()
    progress_dialog = MDDialog(title="Exporting Excel File", auto_dismiss=False)
    progress_dialog.add_widget(progress_bar)

    def __init__(self, **kw) -> None:
        super().__init__(**kw)

        self.config_reader = ConfigReader()
        self.config = self.config_reader.get_sys_config()

    def export_excel_file(self):
        global report_data
        report_name = self.ids.start_date.text + "-to-" + self.ids.end_date.text
        workbook = Workbook()
        sheet = workbook.active
        print(report_data)
        file_path = self.config.get("reports_folder") + "/" + report_name + ".xlsx"
        if report_data is not None:
            if isinstance(report_data, tuple):
                report_data = list(report_data)
            sheet.append(["ATM ID", "ATM Connection", "Uptime %", "Downtime %",
                          "Total Downtime(hh:mm.ss)",
                          "Downtime Reasons", "Report Date"])
            total_rows = len(report_data)

            # Show a processing dialog with a progress bar
            self.progress_dialog.open()

            # Define a function to update the progress bar
            def update_progress(dt):
                if len(report_data) > 0:
                    # Calculate progress percentage
                    progress_percentage = (total_rows - len(report_data)) / total_rows
                    self.progress_bar.value = int(progress_percentage * 100)
                    self.progress_bar.text = f"Progress: {int(progress_percentage * 100)}%"
                    # Remove the first row from report_data
                    report_data.pop(0)
                else:
                    # All rows processed, dismiss the progress dialog
                    self.progress_dialog.dismiss()
                    Clock.unschedule(update_progress)
                    self.show_completion_dialog(f"The Excel file ({report_name}.xlsx) has been exported successfully.",
                                                file_path)

            # Schedule the progress update function to run every 0.1 seconds
            Clock.schedule_interval(update_progress, 0.00001)

            # Export the Excel file in the background
            def export():
                for row in report_data:
                    sheet.append(row)
                workbook.save(file_path)

            from threading import Thread
            Thread(target=export).start()

    def show_completion_dialog(self, message, export_path):
        if not self.dialog:
            open_excel_button = MDFillRoundFlatIconButton(
                text="Open in Excel",
                icon="assets/icons/ic_excel.png",
                text_color=rgba("#a1a1a1"),
                md_bg_color=rgba("#1FC98E"),
                on_release=lambda x: self.open_in_excel(export_path)
            )
            # Check if Excel is installed and enable/disable the button accordingly
            if self.is_excel_installed():
                open_excel_button.disabled = False
            else:
                open_excel_button.disabled = True

            self.dialog = MDDialog(
                title="STD ATM - Spreadsheet Export",
                text=message,
                buttons=[
                    MDFillRoundFlatIconButton(
                        text="Show in Folder",
                        icon="assets/icons/ic_source.png",
                        md_bg_color=rgba("#F2C94C"),
                        text_color=rgba("#a1a1a1"),
                        on_release=lambda x: self.show_in_folder(export_path)
                    ),
                    open_excel_button,
                    MDRoundFlatButton(
                        text="Ok",
                        md_bg_color=rgba("#2D9CDB"),
                        text_color=rgba("#ffffff"),
                        on_release=self.close_dialog
                    ),
                ],
                auto_dismiss=False
            )
        else:
            self.dialog.text = message
        self.dialog.open()

    @staticmethod
    def is_excel_installed():
        # Check if Excel (excel.exe) is available in the system's PATH
        return shutil.which("excel") is not None

    def close_dialog(self, obj):
        self.dialog.dismiss(force=True)
        self.ids.export_xlsx_btn.disabled = True

    @staticmethod
    def show_in_folder(export_path):
        # Open the folder containing the exported file
        folder_path = os.path.dirname(export_path)
        os.startfile(folder_path)

    @staticmethod
    def open_in_excel(export_path):
        # Open the exported file in the default application for Excel files
        subprocess.Popen(["start", "excel", export_path], shell=True)

    def set_start_date(self, instance, value, date_range):
        end = self.ids.end_date.text
        if end == "Select End Date":
            self.ids.date_range.text = f"{value}"
        else:
            self.ids.date_range.text = f"{value} to {end}"
        self.ids.start_date.text = f"{value}"
        self.ids.gen_report_btn.disabled = False

    def set_end_date(self, instance, value, date_range):
        start = self.ids.start_date.text
        if start == "Select Start Date":
            self.ids.date_range.text = f"{value}"
        else:
            self.ids.date_range.text = f"{start} to {value}"
        self.ids.end_date.text = f"{value}"
        self.ids.gen_report_btn.disabled = False

    def on_cancel(self, instance, value):
        """Events called when the "CANCEL" dialog box button is clicked."""

    def select_start_date(self):
        date_dialog = MDDatePicker(title_input="Start Date")
        date_dialog.bind(on_save=self.set_start_date, on_cancel=self.on_cancel)
        date_dialog.open()

    def select_end_date(self):
        date_dialog = MDDatePicker(title_input="End Date")
        date_dialog.bind(on_save=self.set_end_date, on_cancel=self.on_cancel)
        date_dialog.open()
