import hashlib
import logging
import os
import re
import xml.etree.ElementTree as eT

import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pymysql

import app

atm_section_pattern = re.compile(r"UPTIME TOTALS FOR ATM (\d+)")
atm_summary_section_pattern = re.compile(r"ACCUMULATED UPTIME TOTALS FOR *ALL* ATMS")



def log_message(message):
    log_file = app.resource_path("sys_log.log")
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info(message)


def parse_uptime_data(data):
    uptime_info = []
    lines = data.strip().split('\n')

    atm_id = None
    uptime_percent = None
    t_downtime_percent = None
    total_downtime = "00:00.00"
    downtime_reasons = []
    capturing_total_downtime = False
    date_since = None  # Initialize date_since to None

    for index, line in enumerate(lines):
        match = atm_section_pattern.search(line)
        if match:
            if atm_id is not None:
                if not downtime_reasons:
                    downtime_reasons.append(f"No Recorded Reason For ATM-{atm_id}")
                    uptime_percent = 0
                    t_downtime_percent = 0
                downtime_info = ', '.join(downtime_reasons)
                # Add date_since to the uptime_info
                uptime_info.append(
                    [atm_id, uptime_percent, t_downtime_percent, total_downtime, downtime_info, date_since])

            atm_id = match.group(1)
            uptime_percent = 0
            t_downtime_percent = 0
            total_downtime = "00:00.00"
            downtime_reasons = []

        if "Uptime Adjustment" in line:
            capturing_total_downtime = True
            line_index = index
        elif capturing_total_downtime and index == line_index + 2:
            columns = line.split()
            total_downtime = columns[-2]
            t_downtime_percent = columns[-1]
            capturing_total_downtime = False

        if "Online" in line:
            columns = line.split()
            uptime_percent = columns[3]

        # Check for "Totals Since" line and extract the date
        if "Totals Since" in line:
            columns = line.split()
            date_since = columns[2]

        if "ACCUMULATED UPTIME TOTALS FOR *ALL* ATMS" in line:
            break

        if "No totals received from ATM" in line:
            downtime_reasons.append(f"No Totals Received For ATM-{atm_id}")
            uptime_percent = ""

        for reason in [
            "Closed from Sparrow", "Waiting For Comms", "Supervisor",
            "Diagnostics", "Re-entry", "Downloading HCF", "Downloading Other", "Hardware Fault",
            "Power Fail Recovery", "Uptime Adjustment"
        ]:
            if reason in line:
                columns = line.split()
                downtime_percent = columns[-1]
                downtime_reason = f'{reason} ({downtime_percent}%)' if columns[-2] != "0:00.00" else ""
                if downtime_reason:
                    downtime_reasons.append(downtime_reason)

    if atm_id is not None and downtime_reasons:
        downtime_info = ', '.join(downtime_reasons)
        # Add date_since to the uptime_info
        uptime_info.append([atm_id, uptime_percent, t_downtime_percent, total_downtime, downtime_info, date_since])

    return uptime_info


def generate_unique_key(atm_name, since_date):
    combined_string = atm_name + since_date
    unique_key = hashlib.sha256(combined_string.encode()).hexdigest()

    return unique_key


def process_file(file_path):
    config_reader_p = ConfigReader()
    config_p = config_reader_p.get_sys_config()
    try:
        if file_path.endswith(".spa"):
            log_message(
                f"########################## FILE IN TASK: {os.path.basename(file_path)} >> STARTED << "
                f"##############################")
            log_message(
                f"Processing new source file.\nSOURCE FILE NAME  >> {os.path.basename(file_path)}\n"
                f"SOURCES HOME >> {config_p.get('source_folder')}\n")

            with open(file_path, "r+") as file:
                content = file.read()

            uptime_info = parse_uptime_data(content)

            if uptime_info:

                df = pd.DataFrame(uptime_info, columns=["ATM ID", "Uptime %", "Downtime %", "Total Downtime(hh:mm.ss)",
                                                        "Downtime Reasons", "Report Date"])
                excel_file = os.path.splitext(os.path.basename(file_path))[0] + ".xlsx"

                excel_path = os.path.join(config_p.get('reports_folder'), excel_file)
                df.to_excel(excel_path, index=False)
                log_message(f"Report generated.\nREPORT FILE NAME  >> {excel_file}\n"
                            f"REPORTS HOME >> {config_p.get('reports_folder')}\n")
                date_match = re.search(r'\d{8}', excel_file)

                if date_match:
                    date_string = date_match.group()
                    # Convert the date string to a more readable format, if needed
                    formatted_date = f"{date_string[0:4]}-{date_string[4:6]}-{date_string[6:8]}"
                    print("Extracted Date:", formatted_date)
                else:
                    print("Date not found in the filename.")
                file.close()
                # Create a database connection
                db_host = config_p.get("database_host")
                db_user = config_p.get("database_user")
                db_port = config_p.get("database_port")
                db_password = "" if config_p.get("database_password") is None \
                    else config_p.get("database_password")
                db_name = config_p.get("database_name")

                connection = pymysql.connect(host=db_host, port=int(db_port),
                                             user=db_user, password=db_password, db=db_name)

                # Create a cursor
                cursor = connection.cursor()
                # Iterate through the uptime_info and insert data into the database
                for atm_data in uptime_info:
                    atm_id, uptime_percent, t_downtime_percent, total_downtime, downtime_info, date_since = atm_data
                    rec_sha_key = generate_unique_key(atm_id, date_since)
                    # Check if a record with the same rec_sha_key already exists in the database
                    cursor.execute("SELECT * FROM atm_data WHERE rec_sha_key = %s", (rec_sha_key,))
                    existing_record = cursor.fetchone()

                    if not existing_record:
                        # If the record does not exist, insert it into the database
                        # Define the SQL query to insert data into the database
                        insert_query = """INSERT INTO atm_data (atm_id, rec_sha_key, uptime_percent, 
                        t_downtime_percent, total_downtime, downtime_info, date_since) VALUES (%s, %s, %s, %s, %s, 
                        %s, %s)"""

                        # Execute the SQL query
                        cursor.execute(insert_query, (
                            atm_id, rec_sha_key, uptime_percent, t_downtime_percent,
                            total_downtime, downtime_info, formatted_date))

                        # Commit the changes to the database
                        connection.commit()
                    else:
                        log_message(f"Record with rec_sha_key {rec_sha_key} already exists in the database.")

                # Close the cursor and database connection
                cursor.close()
                connection.close()
                completed_path = os.path.join(config_p.get('archive_folder'), os.path.basename(file_path))

                if os.path.exists(completed_path):
                    os.remove(completed_path)

                os.rename(file_path, completed_path)
                log_message(
                    f"Archived processed file: \nARCHIVED FILE NAME  >> {os.path.basename(file_path)}\n"
                    f"ARCHIVES HOME >> {config_p.get('archive_folder')}\n")
                log_message(
                    f"########################## FILE IN TASK: {os.path.basename(file_path)} >> COMPLETED << "
                    f"##############################\n")

    except Exception as e:
        log_message(
            f"########################## FILE IN TASK: {os.path.basename(file_path)} >> STARTED << "
            f"##############################")
        log_message(
            f"\nProcessing new source file.\nSOURCE FILE NAME  >> {os.path.basename(file_path)}\n"
            f"SOURCES HOME >> {config_p.get('source_folder')}\n")
        log_message(f"Error processing file: {os.path.basename(file_path)}")
        log_message(f"Error message: {str(e)}")
        log_message(
            f"########################## FILE IN TASK: {os.path.basename(file_path)} >> COMPLETED << "
            f"##############################\n")


class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".spa"):
            process_file(event.src_path)


class ConfigReader:
    def __init__(self):
        self.xml_file = app.resource_path("config.xml")
        self.sys_config = {}  # Initialize an empty dictionary to store the configuration
        self._observer_state = False

    def get_sys_config(self):
        if not os.path.exists(self.xml_file):
            # Create the XML file with default values if it doesn't exist
            self.create_default_config()

        try:
            tree = eT.parse(self.xml_file)
            root = tree.getroot()

            # Get the configuration type
            config_type = root.get("configuration_type")
            self.sys_config["configuration_type"] = config_type

            # Get the current date
            date_element = root.find("date")
            if date_element is not None:
                current_date = date_element.text
                self.sys_config["current_date"] = current_date

            # Get database configuration
            db_config = root.find("database_configuration")
            if db_config is not None:
                host = db_config.find("host").text
                port = db_config.find("port").text
                name = db_config.find("name").text
                user = db_config.find("user").text
                password = db_config.find("password").text
                self.sys_config["database_host"] = host
                self.sys_config["database_port"] = port
                self.sys_config["database_name"] = name
                self.sys_config["database_user"] = user
                self.sys_config["database_password"] = password

            # Get working directories
            working_dirs = root.find("working_directories")
            if working_dirs is not None:
                source_folder = working_dirs.find("source_folder").text
                reports_folder = working_dirs.find("reports_folder").text
                archive_folder = working_dirs.find("archive_folder").text
                self.sys_config["source_folder"] = source_folder
                self.sys_config["reports_folder"] = reports_folder
                self.sys_config["archive_folder"] = archive_folder

        except eT.ParseError as e:
            print("Error parsing XML:", e)

        return self.sys_config

    def observer_sate(self, state):
        root_element = eT.Element("observer_config")
        observer = eT.SubElement(root_element, "state")
        observer.text = state
        tree = eT.ElementTree(root_element)
        tree.write(app.resource_path("observer.xml"), encoding="utf-8", xml_declaration=True)

    def get_state(self):

        if not os.path.exists("observer.xml"):
            self.observer_sate("Off")
        tree = eT.parse(app.resource_path("observer.xml"))
        root = tree.getroot()

        state_element = root.find("state")
        if state_element is not None:
            if state_element.text == "On":
                self._observer_state = True
                return True
            else:
                self._observer_state = False
                return False
        else:
            self._observer_state = False
            return False

    def start_observer(self):

        observer = Observer()
        event_handler = MyHandler()
        # Check if the observer is already running
        state = self.get_state()
        print(state)
        if not state:
            sys_conf = self.get_sys_config()
            observer.schedule(event_handler, path=sys_conf.get("source_folder"), recursive=False)
            log_message(f"ATM Reporter Started >> [SOURCES FOLDER >> {sys_conf.get('source_folder')}]")
            observer.start()
            print(self.get_state())
            self._observer_state = True
            self.observer_sate("On")
        else:
            log_message("Observer is already running.")

        _existing_files_ = [os.path.join(config.get('source_folder'), filename)
                            for filename in os.listdir(config.get('source_folder'))]
        for _existing_file_ in _existing_files_:
            process_file(_existing_file_)

        for _folder_ in [config.get('archive_folder'), config.get('reports_folder')]:
            if not os.path.exists(_folder_):
                os.makedirs(_folder_)

    def restart_observer(self):
        sys_conf = self.get_sys_config()
        # Check if the observer is already running
        observer = Observer()
        event_handler = MyHandler()
        if not self.get_state():
            observer.schedule(event_handler, path=self.sys_config.get("source_folder"), recursive=False)
            log_message(f"Watchdog File Observer Restarted >> [SOURCES FOLDER >>"
                        f" {self.sys_config.get('source_folder')}]")
            observer.start()
            self._observer_state = True
            self.observer_sate("On")
        else:
            observer.stop()
            observer.schedule(event_handler, path=sys_conf.get("source_folder"), recursive=False)
            log_message(f"Watchdog File Observer Restarted >> [SOURCES FOLDER >>"
                        f" {sys_conf.get('source_folder')}]")
            observer.start()
            self._observer_state = True
            self.observer_sate("Off")

    def stop_observer(self):
        observer = Observer()
        print(self._observer_state)
        log_message(f"Watchdog File Observer stopped")
        os.remove("observer.xml")
        observer.stop()

    def create_default_config(self):
        # Create the XML file with default values
        root = eT.Element("configurations")
        root.set("configuration_type", "default")

        # Add the current date as an element
        current_date = eT.SubElement(root, "date")
        current_date.text = ""

        # Database Configuration
        db_config = eT.SubElement(root, "database_configuration")
        eT.SubElement(db_config, "host").text = "localhost"
        eT.SubElement(db_config, "port").text = "3306"
        eT.SubElement(db_config, "name").text = "atm_data"
        eT.SubElement(db_config, "user").text = "root"
        eT.SubElement(db_config, "password").text = "Default"

        # Working Directories
        working_dirs = eT.SubElement(root, "working_directories")
        eT.SubElement(working_dirs, "source_folder").text = "source"
        eT.SubElement(working_dirs, "reports_folder").text = "reports"
        eT.SubElement(working_dirs, "archive_folder").text = "completed"

        tree = eT.ElementTree(root)
        tree.write(self.xml_file, encoding="utf-8", xml_declaration=True)

    def create_database_connection(self):
        sys_conf = self.get_sys_config()
        print(f"Here: {sys_conf}")
        # Get database connection parameters from the config dictionary
        host = sys_conf.get("database_host")
        port = sys_conf.get("database_port")
        user = sys_conf.get("database_user")
        password = sys_conf.get("database_password")
        db_name = sys_conf.get("database_name")

        try:
            # Create a database connection
            connection = pymysql.connect(host=f"{host}", port=int(port),
                                         user=f"{user}", password=password, db=f"{db_name}")
            cursor = connection.cursor()
            return connection, cursor, f"Database connection successful."
        except Exception as e:
            msg = f"Error creating database connection:", e
            return None, None, msg

    def test_database_connection(self):
        # Attempt to create a test database connection
        connection, cursor, msg = self.create_database_connection()

        if connection is not None:
            # Perform a simple test query (e.g., fetching a version)
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            # Close the test connection
            connection.close()
            sys_conf = self.get_sys_config()
            return f"Database connection established successfully\n\n" \
                   f"Version:{version[0]}\n" \
                   f"Host: {sys_conf.get('database_host')}\n" \
                   f"Port: {sys_conf.get('database_port')}\n" \
                   f"Name: {sys_conf.get('database_name')}\n" \
                   f"User: {sys_conf.get('database_user')}\n" \
                   f"Password: {sys_conf.get('database_password')}"
        else:
            print(msg)
            return f"Database connection could not be established.\n" \
                   f"Message: {msg}"


config_reader = ConfigReader()
config = config_reader.get_sys_config()

existing_files = [os.path.join(config.get('source_folder'), filename)
                  for filename in os.listdir(config.get('source_folder'))]
for existing_file in existing_files:
    process_file(existing_file)

for folder in [config.get('archive_folder'), config.get('reports_folder')]:
    if not os.path.exists(folder):
        os.makedirs(folder)
