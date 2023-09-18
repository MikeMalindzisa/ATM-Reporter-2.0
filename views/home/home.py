import datetime
import re

import pymysql
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp
from kivy.utils import rgba, QueryDict
from kivy.clock import Clock

import numpy as np
from scipy.interpolate import make_interp_spline
import matplotlib as mpl
import matplotlib.pyplot as plt

from config import ConfigReader
from widgets.kivyplt import MatplotFigure

Builder.load_file('views/home/home.kv')


def time_format(time_string):
    # Use regular expression to find the time components
    match = re.search(r'(\d+:\d+:\d+\.\d+)', str(time_string))

    if match:
        time_parts = match.group(1).split(":")
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2].split(".")[0])
        fractions = float("0." + time_parts[2].split(".")[1])

        # Format the time as "HH:MM:SS.SS"
        return f"{hours:02}:{minutes:02}:{seconds:02}.{fractions:.2f}"
    else:
        return "00:00.00"


class Home(BoxLayout):
    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        Clock.schedule_once(self.render, .1)
        config_reader = ConfigReader()
        self.config = config_reader.get_sys_config()

    def render(self, _):
        self.ids.as_at_date.text = datetime.datetime.now().strftime('%A, %d %B %Y')
        x = np.array([x for x in range(12)])
        xlabels = ['', 'Jul 22', 'Aug 22', 'Sept 22', 'Oct 22', 'Nov 22', "Dec 22", 'Jan 23', 'Feb 23', 'Mar 23',
                   'Apr 23', 'May 23', 'Jun 23']
        y = np.array([83, 88, 96, 94, 87, 91, 73, 77, 84, 89, 93, 98])
        b = np.array([97, 99, 96, 98, 97, 91, 95, 99, 98, 99, 96, 98])

        xy_spline = make_interp_spline(x, y)
        xy_spline2 = make_interp_spline(x, b)
        x1 = np.linspace(x.min(), x.max(), 500)
        y1 = xy_spline(x1)
        y2 = xy_spline2(x1)

        chart = mpl.figure.Figure(figsize=(2, 2))
        chart.gca().spines['top'].set_visible(False)
        chart.gca().spines['right'].set_visible(False)
        chart.gca().spines['left'].set_visible(True)
        chart.gca().set_xticklabels(xlabels)
        chart.gca().plot(x1, y1)
        chart.gca().plot(x1, y2)

        plot = MatplotFigure(chart)
        plot.pos = [-2, 0]
        self.ids.graph.clear_widgets()
        self.ids.graph.add_widget(plot)
        self.widgets_setup()

    def widgets_setup(self):
        host = self.config.get("database_host")
        user = self.config.get("database_user")
        password = "" if self.config.get("database_password") is None \
            else self.config.get("database_password")
        db_name = self.config.get("database_name")
        try:
            connection = pymysql.connect(host=host, user=user, password=password, db=db_name)

            # Create a cursor
            cursor = connection.cursor()
            query = "SELECT * FROM atm_data_summary"
            # print(query)
            cursor.execute(query)

            atm_report_data = cursor.fetchone()
            fibre_con = atm_report_data[11]
            lte_con = atm_report_data[10]
            lte_av_up = atm_report_data[8]
            fibre_av_up = atm_report_data[9]

            total_downtime = atm_report_data[2]
            avg_uptime_percent = atm_report_data[0]

            downtime = time_format(total_downtime)

            self.ids.fibre_connections.text = f"{fibre_con} ATMs"
            self.ids.lte_connections.text = f"{lte_con} ATMs"
            self.ids.total_downtime_time.text = f"{downtime}"
            self.ids.lte_av_uptime_percent.text = "{:.2f}".format(lte_av_up) + " %"
            self.ids.fibre_av_uptime_percent.text = "{:.2f}".format(fibre_av_up) + " %"
            self.ids.avg_uptime_percent.text = "{:.2f}".format(avg_uptime_percent) + " %"

        except pymysql.connect.Error as err:
            print("Error: {}".format(err))
