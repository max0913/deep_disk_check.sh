Deep Disk Check

Deep Disk Check is a comprehensive Python script designed for Mac Minis to perform in-depth, non-interactive checks of all connected disk drives. It meticulously scans various filesystem types, logs errors, documents issues requiring manual intervention, and provides summary recommendations upon completion. This tool is essential for system administrators and power users aiming to maintain the integrity and performance of their disk drives.

Table of Contents

Features
Prerequisites
Installation
Usage
Interactive Mode
Non-Interactive Mode
Dry Run Mode
Logging
Scheduling with Cron
Troubleshooting
Contributing
License
Acknowledgments
Features

Comprehensive Disk Scanning: Detects and checks all external physical disks excluding system disks.
Filesystem Support: Compatible with a wide range of macOS filesystems, including APFS, HFS+, FAT32, exFAT, and more.
Robust Logging:
Specification Log (spec-YYYYMMDD-HHMMSS.log): Records all informational messages and detected disk errors.
Error Log (error-YYYYMMDD-HHMMSS.log): Captures errors requiring manual intervention and appends summary recommendations.
Execution Modes:
Interactive Mode: Offers a user-friendly menu to select execution options.
Non-Interactive Mode: Runs without prompts, ideal for automation.
Dry Run Mode: Simulates actions without making changes, useful for testing.
Error Handling: Gracefully manages missing dependencies, permission issues, and unexpected interruptions.
Extensibility: Easily add support for additional filesystem types or new features.
Performance Optimization: Efficiently handles multiple or large disk drives to minimize execution time.
Prerequisites

Python 3.6 or Higher: Ensure Python 3 is installed on your Mac Mini.
python3 --version
If not installed, download it from the official website.
Required System Commands: The script relies on several system commands, typically available on macOS by default:
diskutil
grep
awk
mkdir
touch
tee
date
echo
sleep
Verify their presence:

which diskutil grep awk mkdir touch tee date echo sleep
If any commands are missing, install them or ensure they're included in your system's PATH.
Root Privileges: The script performs disk operations and requires root access. Ensure you have sudo privileges.
Installation

Clone the Repository
git clone https://github.com/yourusername/deep-disk-check.git
cd deep-disk-check
Set Up the Script
Download the Script
Save the deep_disk_check.py script from this repository to your local machine.
Make the Script Executable
chmod +x deep_disk_check.py
Create Log Directory
Ensure the log directory exists with appropriate permissions:

sudo mkdir -p /var/log/disk_checks
sudo chmod 755 /var/log/disk_checks
Usage

Deep Disk Check can be executed in three modes: Interactive, Non-Interactive, and Dry Run. Below are detailed instructions for each mode.

Interactive Mode
By default, running the script without any arguments launches it in interactive mode, presenting a menu for user options.

Run the Script:

sudo ./deep_disk_check.py
Interactive Menu Options:

Select an option:
1) Run normally
2) Dry run (simulate actions without making changes)
3) Exit
Enter your choice [1-3]:
Option 1: Executes the disk check normally, performing actual unmounting, verification, and repair operations.
Option 2: Performs a dry run, simulating actions without making any changes to the disks.
Option 3: Exits the script.
Non-Interactive Mode
Ideal for automation or scheduling via cron jobs. The script runs without any user prompts.

Run Normally:

sudo ./deep_disk_check.py --non-interactive
Dry Run Mode
Simulates the disk check actions without making any changes, useful for testing.

Run Dry Run:

sudo ./deep_disk_check.py --dry-run
Note: The --dry-run and --non-interactive options are mutually exclusive.

Logging

The script maintains two primary log files in the /var/log/disk_checks/ directory:

Specification Log (spec-YYYYMMDD-HHMMSS.log):
Contains all informational messages, actions performed, and detected disk errors.
Includes real-time output to the terminal for immediate feedback.
Error Log (error-YYYYMMDD-HHMMSS.log):
Captures errors that require manual intervention.
Appends a summary of recommendations upon completion.
Example Log Filenames:

spec-20250106-143500.log
error-20250106-143500.log
Viewing Logs:

Use less or any text editor to view the logs.

sudo less /var/log/disk_checks/spec-YYYYMMDD-HHMMSS.log
sudo less /var/log/disk_checks/error-YYYYMMDD-HHMMSS.log
Replace YYYYMMDD-HHMMSS with the actual timestamp of the log files.

Scheduling with Cron

Automate disk checks by scheduling the script using cron. Below is an example of how to set up a daily disk check at 2 AM.

Edit the Crontab:
sudo crontab -e
Add a Cron Job:
0 2 * * * /path/to/deep_disk_check.py --non-interactive
Replace /path/to/ with the actual path where the script is located.
Save and Exit:
The cron job will now execute the script as scheduled.
Note: Ensure that the script has executable permissions and the log directory exists.

Troubleshooting

Common Issues
Missing Required Commands
Symptom: The script logs errors about missing commands and exits gracefully.

Solution:

Verify the presence of required commands using:
which diskutil grep awk mkdir touch tee date echo sleep
If any commands are missing, install them or ensure they're included in your system's PATH.
Insufficient Permissions
Symptom: The script logs an error stating it must be run as root and exits.

Solution:

Run the script with sudo:
sudo ./deep_disk_check.py
Disk Unmounting Failures
Symptom: Errors when attempting to unmount disks, possibly due to them being in use.

Solution:

Ensure no applications are using the disks.
Manually unmount the disks if necessary.
Review the error log for specific details.
Log Directory Issues
Symptom: Errors related to log file creation or access.

Solution:

Ensure the log directory exists and has appropriate permissions:
sudo mkdir -p /var/log/disk_checks
sudo chmod 755 /var/log/disk_checks
Advanced Troubleshooting
Reviewing Logs: Always check both specification and error logs for detailed information.
Script Modifications: Ensure that any modifications to the script maintain its integrity and functionality.
System Updates: Keeping your macOS and Python environment updated can prevent compatibility issues.
Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes, feel free to open an issue or submit a pull request.

Fork the Repository
Create a New Branch
git checkout -b feature/YourFeatureName
Commit Your Changes
git commit -m "Add Your Feature"
Push to the Branch
git push origin feature/YourFeatureName
Open a Pull Request
Provide a clear description of your changes and the motivation behind them.
License

This project is licensed under the MIT License.

Acknowledgments

Inspired by the need for robust disk maintenance tools for macOS environments.
Thanks to the open-source community for their invaluable resources and support.
Disclaimer: Always ensure you have adequate backups before performing disk operations to prevent potential data loss.

Instructions to Create README.md
Open Terminal and navigate to your project directory:
cd /path/to/your/project
Create or Open README.md using a text editor like nano:
nano README.md
Paste the Content:
Copy all the text from the "README.md Content" section above.
Paste it into the nano editor by right-clicking or using the paste shortcut (Cmd + V).
Save and Exit:
In nano, press Ctrl + O to write out (save) the file.
Press Enter to confirm.
Press Ctrl + X to exit the editor.
Verify the README.md:
cat README.md
Ensure that the content appears correctly formatted.
Final Notes
Customization: Replace yourusername in the repository URL and badges with your actual GitHub username.
Badges: Update or add relevant badges based on your project's status and technologies.
License: Ensure you include a proper LICENSE file in your repository if you reference one.
Screenshots: Consider adding screenshots or GIFs demonstrating the script in action for better user understanding.
Contribution Guidelines: You might want to add a CONTRIBUTING.md file for detailed contribution guidelines.
Issues and Pull Requests: Encourage users to open issues for bugs or feature requests and to submit pull requests for improvements.
