# ATM Reporter

**Author:** Mike Malindzisa  
**Email:** machaweml@gmail.com

## Description

The ATM Reporter is an automation tool designed to streamline the process of generating Excel reports from .spa ATM report log files generated daily. It monitors a specified folder for incoming source files using Watchdog, a file system monitoring library. When a new file is detected, the system automatically extracts data from the .spa file and compiles it into an Excel report.

Additionally, the ATM Reporter populates a SQL database with relevant data from each reportable line item, ensuring that historical information is readily accessible.

The system features a narrative dashboard that provides valuable insights by comparing ATM Uptime and Downtime statistics for both fiber and LTE connections. Users can filter database data using date ranges to populate a datatable and download customized data in an Excel report format.

In essence, the ATM Reporter simplifies and automates the process of managing ATM report data, making it a valuable tool for efficient data analysis and reporting within a private project environment.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.11**
- **certifi==2021.10.8**
- **charset-normalizer==2.0.12**
- **cycler==0.11.0**
- **docutils==0.18.1**
- **fonttools==4.31.1**
- **idna==3.3**
- **Kivy~=2.2.1**
- **Kivy-Garden==0.1.4**
- **kiwisolver==1.4.0**
- **matplotlib~=3.7.2**
- **numpy~=1.25.2**
- **packaging==21.3**
- **Pillow~=10.0.0**
- **pkg_resources==0.0.0**
- **Pygments==2.11.2**
- **pyparsing==3.0.7**
- **python-dateutil==2.8.2**
- **requests==2.27.1**
- **scipy~=1.11.2**
- **six==1.16.0**
- **urllib3==1.26.9**
- **pandas~=2.1.0**
- **kivymd~=1.2.0.dev0**
- **openpyxl~=3.1.2**
- **KivyCalendar~=0.1.3**
- **PyMySQL~=1.1.0**
- **watchdog~=3.0.0**

Please make sure to have these Python packages installed before running the ATM Reporter application.

## Usage

To use the ATM Reporter, follow these simple steps:

1. **Run the Application:** When you run the application for the first time, default configurations will be applied.

2. **Upload SPA Files:**
   - Place your .spa ATM report log files in the source folder.
   
3. **Browse and Download Generated Reports:**
   - Navigate to the "Generated Reports" tab.
   - Browse and download the generated reports as needed.

4. **Generating Custom Reports:**
   - Open the "Report Filter" tab.
   - Enter the start date and end date for your custom report.
   - Click the "Generate Report" button.
   - Click "Export Excel" and wait for the process to complete (duration depends on the dataframe size).

5. **Customizing Settings - Database Connection:**
   - Open the "Settings" tab.
   - If the "Use Default Configurations" checkbox is checked, uncheck it.
   - Set the database host, port, database name, database user, and password.
   - Click "Save Configurations."
   - You can click "Test Connection" to verify the database connection. This may require an application restart.

6. **Customizing Settings - Working Directories:**
   - Open the "Settings" tab.
   - If the "Use Default Configurations" checkbox is checked, uncheck it.
   - Set the source folder, reports folder, and archive folder as desired.
   - Click "Save Configurations."
   - This may require an application restart.

Follow these steps to effectively use and customize the ATM Reporter for your needs.
