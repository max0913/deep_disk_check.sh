# Deep Disk Check

Deep Disk Check is a comprehensive Python script designed for Mac Minis to perform in-depth, non-interactive checks of all connected disk drives. It meticulously scans various filesystem types, logs errors, documents issues requiring manual intervention, and provides summary recommendations upon completion. This tool is essential for system administrators and power users aiming to maintain the integrity and performance of their disk drives.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Non-Interactive Mode](#non-interactive-mode)
  - [Dry Run Mode](#dry-run-mode)
- [Logging](#logging)
- [Scheduling with Cron](#scheduling-with-cron)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

- **Comprehensive Disk Scanning**: Detects and checks all external physical disks excluding system disks.
- **Filesystem Support**: Compatible with a wide range of macOS filesystems, including APFS, HFS+, FAT32, exFAT, and more.
- **Robust Logging**:
  - Specification Log (spec-YYYYMMDD-HHMMSS.log): Records all informational messages and detected disk errors.
  - Error Log (error-YYYYMMDD-HHMMSS.log): Captures errors requiring manual intervention and appends summary recommendations.
- **Execution Modes**:
  - Interactive Mode: Offers a user-friendly menu to select execution options.
  - Non-Interactive Mode: Runs without prompts, ideal for automation.
  - Dry Run Mode: Simulates actions without making changes, useful for testing.
- **Error Handling**: Gracefully manages missing dependencies, permission issues, and unexpected interruptions.
- **Extensibility**: Easily add support for additional filesystem types or new features.
- **Performance Optimization**: Efficiently handles multiple or large disk drives to minimize execution time.

## Prerequisites

- **Python 3.6 or Higher**: Ensure Python 3 is installed on your Mac Mini.

  ```bash
  python3 --version
  ```
  If not installed, download it from the official website.

- **Required System Commands**: The script relies on several system commands, typically available on macOS by default:
  - `diskutil`
  - `grep`
  - `awk`
  - `mkdir`
  - `touch`
  - `tee`
  - `date`
  - `echo`
  - `sleep`

  Verify their presence:

  ```bash
  which diskutil grep awk mkdir touch tee date echo sleep
  ```
  If any commands are missing, install them or ensure they're included in your system's PATH.

- **Root Privileges**: The script performs disk operations and requires root access. Ensure you have sudo privileges.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/deep-disk-check.git
   cd deep-disk-check
   ```

2. **Set Up the Script**:

   - Download the `deep_disk_check.py` script from this repository to your local machine.

3. **Make the Script Executable**:

   ```bash
   chmod +x deep_disk_check.py
   ```

4. **Create Log Directory**:

   Ensure the log directory exists with appropriate permissions:

   ```bash
   sudo mkdir -p /var/log/disk_checks
   sudo chmod 755 /var/log/disk_checks
   ```

## Usage

Deep Disk Check can be executed in three modes: Interactive, Non-Interactive, and Dry Run. Below are detailed instructions for each mode.

### Interactive Mode

By default, running the script without any arguments launches it in interactive mode, presenting a menu for user options.

Run the Script:

```bash
sudo ./deep_disk_check.py
```

Interactive Menu Options:

```
Select an option:
1) Run normally
2) Dry run (simulate actions without making changes)
3) Exit
Enter your choice [1-3]:
```

- Option 1: Executes the disk check normally, performing actual unmounting, verification, and repair operations.
- Option 2: Performs a dry run, simulating actions without making any changes to the disks.
- Option 3: Exits the script.

### Non-Interactive Mode

Ideal for automation or scheduling via cron jobs. The script runs without any user prompts.

Run Normally:

```bash
sudo ./deep_disk_check.py --non-interactive
```

### Dry Run Mode

Simulates the disk check actions without making any changes, useful for testing.

Run Dry Run:

```bash
sudo ./deep_disk_check.py --dry-run
```

**Note**: The `--dry-run` and `--non-interactive` options are mutually exclusive.

## Logging

The script maintains two primary log files in the `/var/log/disk_checks/` directory:

- **Specification Log (spec-YYYYMMDD-HHMMSS.log)**:
  - Contains all informational messages, actions performed, and detected disk errors.
  - Includes real-time output to the terminal for immediate feedback.
- **Error Log (error-YYYYMMDD-HHMMSS.log)**:
  - Captures errors that require manual intervention.
  - Appends a summary of recommendations upon completion.

Example Log Filenames:

- `spec-20250106-143500.log`
- `error-20250106-143500.log`

Viewing Logs:

```bash
sudo less /var/log/disk_checks/spec-YYYYMMDD-HHMMSS.log
sudo less /var/log/disk_checks/error-YYYYMMDD-HHMMSS.log
```

Replace `YYYYMMDD-HHMMSS` with the actual timestamp of the log files.

## Scheduling with Cron

Automate disk checks by scheduling the script using cron. Below is an example of how to set up a daily disk check at 2 AM.

1. **Edit the Crontab**:

   ```bash
   sudo crontab -e
   ```

2. **Add a Cron Job**:

   ```bash
   0 2 * * * /path/to/deep_disk_check.py --non-interactive
   ```

   Replace `/path/to/` with the actual path where the script is located.

3. **Save and Exit**:

   The cron job will now execute the script as scheduled.

   **Note**: Ensure that the script has executable permissions and the log directory exists.

## Troubleshooting

### Common Issues

#### Missing Required Commands

- **Symptom**: The script logs errors about missing commands and exits gracefully.

- **Solution**:

  Verify the presence of required commands using:

  ```bash
  which diskutil grep awk mkdir touch tee date echo sleep
  ```
  If any commands are missing, install them or ensure they're included in your system's PATH.

#### Insufficient Permissions

- **Symptom**: The script logs an error stating it must be run as root and exits.

- **Solution**:

  Run the script with sudo:

  ```bash
  sudo ./deep_disk_check.py
  ```

#### Disk Unmounting Failures

- **Symptom**: Errors when attempting to unmount disks, possibly due to them being in use.

- **Solution**:

  Ensure no applications are using the disks.
  Manually unmount the disks if necessary.
  Review the error log for specific details.

#### Log Directory Issues

- **Symptom**: Errors related to log file creation or access.

- **Solution**:

  Ensure the log directory exists and has appropriate permissions:

  ```bash
  sudo mkdir -p /var/log/disk_checks
  sudo chmod 755 /var/log/disk_checks
  ```

### Advanced Troubleshooting

- Reviewing Logs: Always check both specification and error logs for detailed information.
- Script Modifications: Ensure that any modifications to the script maintain its integrity and functionality.
- System Updates: Keeping your macOS and Python environment updated can prevent compatibility issues.

## Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes, feel free to open an issue or submit a pull request.

1. **Fork the Repository**
2. **Create a New Branch**:

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**:

   ```bash
   git commit -m "Add Your Feature"
   ```

4. **Push to the Branch**:

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**: Provide a clear description of your changes and the motivation behind them.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Inspired by the need for robust disk maintenance tools for macOS environments.
- Thanks to the open-source community for their invaluable resources and support.

**Disclaimer**: Always ensure you have adequate backups before performing disk operations to prevent potential data loss.
