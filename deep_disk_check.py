#!/usr/bin/env python3

"""
Script: deep_disk_check.py
Description:
    Performs a deep check of all disk drives on a Mac Mini.
    Logs the results, documents any errors requiring manual intervention,
    and provides a summary of recommendations.
"""

import os
import subprocess
import sys
import argparse
import logging
from datetime import datetime
import atexit
import signal

# ------------------------ Configuration ------------------------

# Define the log directory
LOGDIR = "/var/log/disk_checks"

# Define required commands
REQUIRED_COMMANDS = ["diskutil", "grep", "awk", "mkdir", "touch", "tee", "date", "echo", "sleep"]

# Supported filesystem types
SUPPORTED_FILESYSTEMS = [
    "apfs", "hfs", "msdos", "exfat", "udf", "ufs", "ntfs",
    "fat32", "ext4", "btrfs", "xfs", "iso9660", "smbfs",
    "davfs2", "fuseblk", "fuse"
]

# ------------------------ Global Variables ------------------------

UNMOUNTED_DISKS = []
CLEANUP_DONE = False

# ------------------------ Functions ----------------------------

def setup_logging():
    """
    Sets up logging for informational and error messages with timestamps.
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    spec_log_filename = os.path.join(LOGDIR, f"spec-{timestamp}.log")
    error_log_filename = os.path.join(LOGDIR, f"error-{timestamp}.log")
    
    # Create log directory if it doesn't exist
    os.makedirs(LOGDIR, exist_ok=True)
    
    # Configure spec logger
    spec_logger = logging.getLogger('spec_logger')
    spec_logger.setLevel(logging.INFO)
    spec_handler = logging.FileHandler(spec_log_filename)
    spec_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    spec_logger.addHandler(spec_handler)
    
    # Stream handler for spec logger (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    spec_logger.addHandler(stream_handler)
    
    # Configure error logger
    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.ERROR)
    error_handler = logging.FileHandler(error_log_filename)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    error_logger.addHandler(error_handler)
    
    return spec_logger, error_logger

def log_info(message, spec_logger):
    """
    Logs informational messages.
    """
    spec_logger.info(message)

def log_error(message, spec_logger, error_logger):
    """
    Logs error messages to both spec and error logs.
    """
    error_logger.error(message)
    spec_logger.error(message)

def command_exists(command):
    """
    Checks if a command exists on the system by searching through the PATH.
    """
    return subprocess.call(['which', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def check_required_commands(spec_logger, error_logger):
    """
    Verifies that all required commands are available.
    """
    missing_cmds = []
    for cmd in REQUIRED_COMMANDS:
        if not command_exists(cmd):
            missing_cmds.append(cmd)
    
    if missing_cmds:
        for cmd in missing_cmds:
            log_error(f"Required command '{cmd}' not found or not executable.", spec_logger, error_logger)
        # Additionally, provide PATH information
        current_path = os.environ.get('PATH', '')
        log_error(f"Current PATH: {current_path}", spec_logger, error_logger)
        log_error("One or more required commands are missing. Please install them or ensure they are in your PATH.", spec_logger, error_logger)
        sys.exit("Missing required commands. Check error logs for details.")

def ensure_root(spec_logger, error_logger):
    """
    Ensures the script is run with root privileges.
    """
    if os.geteuid() != 0:
        log_error("This script must be run as root. Please use sudo.", spec_logger, error_logger)
        sys.exit("Insufficient permissions. Exiting.")

def get_filesystem(disk, spec_logger, error_logger):
    """
    Determines the filesystem type of a given disk.
    """
    try:
        result = subprocess.run(['diskutil', 'info', disk], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if "Type (Bundle)" in line:
                fs_type = line.split(":")[1].strip().lower()
                log_info(f"Detected filesystem type for {disk}: {fs_type}", spec_logger)
                return fs_type
        log_error(f"Filesystem type not found for {disk}.", spec_logger, error_logger)
        return "unknown"
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to get filesystem info for {disk}. Error: {e.stderr.strip()}", spec_logger, error_logger)
        return "unknown"

def get_external_disks(spec_logger, error_logger):
    """
    Retrieves a list of external physical disks excluding system disks.
    """
    try:
        result = subprocess.run(['diskutil', 'list', 'external', 'physical'], capture_output=True, text=True, check=True)
        disks = []
        for line in result.stdout.splitlines():
            if line.startswith("/dev/disk"):
                disk = line.split()[0]
                if not is_system_disk(disk, spec_logger, error_logger):
                    disks.append(disk)
        log_info(f"Found external disks: {', '.join(disks) if disks else 'None'}", spec_logger)
        return disks
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to list external physical disks. Error: {e.stderr.strip()}", spec_logger, error_logger)
        return []

def is_system_disk(disk, spec_logger, error_logger):
    """
    Checks if a disk is a system disk to prevent accidental modifications.
    """
    try:
        result = subprocess.run(['diskutil', 'list'], capture_output=True, text=True, check=True)
        system_partitions = [line.split()[0] for line in result.stdout.splitlines() if "Apple_APFS" in line or "Apple_HFS" in line]
        for sys_disk in system_partitions:
            if sys_disk.startswith(disk):
                log_info(f"{disk} is identified as a system disk.", spec_logger)
                return True
        return False
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to determine if {disk} is a system disk. Error: {e.stderr.strip()}", spec_logger, error_logger)
        return False

def unmount_disk(disk, mode, spec_logger, error_logger):
    """
    Attempts to unmount a disk if it is mounted.
    """
    try:
        result = subprocess.run(['diskutil', 'info', disk], capture_output=True, text=True, check=True)
        mounted = False
        for line in result.stdout.splitlines():
            if line.startswith("Mounted:"):
                mounted = "Yes" in line
                break
        if mounted:
            if mode == "dry":
                log_info(f"Dry run: Would attempt to unmount {disk}.", spec_logger)
                return True
            log_info(f"{disk} is mounted. Attempting to unmount...", spec_logger)
            subprocess.run(['diskutil', 'unmountDisk', disk], check=True, capture_output=True)
            log_info(f"{disk} unmounted successfully.", spec_logger)
            UNMOUNTED_DISKS.append(disk)
            return True
        else:
            log_info(f"{disk} is not mounted. No need to unmount.", spec_logger)
            return True
    except subprocess.CalledProcessError as e:
        log_error(f"Unable to unmount {disk}. It may be in use. Skipping verification. Error: {e.stderr.strip()}", spec_logger, error_logger)
        return False

def mount_disk(disk, mode, spec_logger, error_logger):
    """
    Attempts to remount a disk if it was previously unmounted.
    """
    try:
        if mode == "dry":
            log_info(f"Dry run: Would attempt to remount {disk}.", spec_logger)
            return
        log_info(f"Attempting to remount {disk}...", spec_logger)
        subprocess.run(['diskutil', 'mountDisk', disk], check=True, capture_output=True)
        log_info(f"{disk} remounted successfully.", spec_logger)
        UNMOUNTED_DISKS.remove(disk)
    except subprocess.CalledProcessError as e:
        log_error(f"Unable to remount {disk}. You may need to remount it manually. Error: {e.stderr.strip()}", spec_logger, error_logger)

def verify_filesystem(disk, fs_type, mode, spec_logger, error_logger):
    """
    Verifies and repairs the filesystem of a disk based on its type.
    """
    if fs_type not in SUPPORTED_FILESYSTEMS:
        log_error(f"Unsupported or unknown filesystem type '{fs_type}' for {disk}. Skipping verification.", spec_logger, error_logger)
        return
    
    if mode == "dry":
        log_info(f"Dry run: Would verify {disk} with filesystem type {fs_type}.", spec_logger)
        return
    
    log_info(f"Verifying {disk} with filesystem type {fs_type}...", spec_logger)
    try:
        subprocess.run(['diskutil', 'verifyVolume', disk], check=True, capture_output=True)
        log_info(f"{disk} verification succeeded.", spec_logger)
    except subprocess.CalledProcessError as e:
        log_error(f"{disk} verification found issues: {e.stderr.strip()}", spec_logger, error_logger)
        log_info(f"Attempting to repair {disk}...", spec_logger)
        try:
            subprocess.run(['diskutil', 'repairVolume', disk], check=True, capture_output=True)
            log_info(f"{disk} repair succeeded.", spec_logger)
        except subprocess.CalledProcessError as repair_error:
            log_error(f"Error: {disk} repair failed. Manual intervention may be required: {repair_error.stderr.strip()}", spec_logger, error_logger)

def append_summary(spec_logger, error_logger):
    """
    Appends a summary of recommendations to the error log.
    """
    try:
        error_log_file = error_logger.handlers[0].baseFilename
        with open(error_log_file, 'r') as f:
            error_content = f.read()
        with open(error_log_file, 'a') as f:
            f.write("\n===== Summary of Recommendations =====\n")
            if "ERROR" in error_content:
                f.write("Some disks encountered issues that require manual intervention. Please review the above errors and take appropriate actions.\n")
                spec_logger.info("Summary: Some errors were encountered during the disk check. Please review the error logs for details.")
            else:
                f.write("All disk checks completed without errors.\n")
                spec_logger.info("Summary: No errors detected. All disk checks passed successfully.")
    except Exception as e:
        log_error(f"Failed to append summary to error log: {str(e)}", spec_logger, error_logger)

def cleanup(spec_logger, error_logger):
    """
    Performs cleanup operations such as remounting disks and appending summary.
    """
    global CLEANUP_DONE
    if not CLEANUP_DONE:
        log_info("Script interrupted or exiting. Performing cleanup.", spec_logger)
        for disk in UNMOUNTED_DISKS.copy():
            mount_disk(disk, mode="normal", spec_logger=spec_logger, error_logger=error_logger)
        append_summary(spec_logger, error_logger)
        CLEANUP_DONE = True
    sys.exit(1)

def show_interactive_menu(mode_container):
    """
    Displays an interactive menu for user options.
    """
    while True:
        print("\nSelect an option:")
        print("1) Run normally")
        print("2) Dry run (simulate actions without making changes)")
        print("3) Exit")
        choice = input("Enter your choice [1-3]: ").strip()
        if choice == "1":
            mode_container['mode'] = "normal"
            break
        elif choice == "2":
            mode_container['mode'] = "dry"
            break
        elif choice == "3":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")

def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Deep Disk Check Script for Mac Mini")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true', help='Simulate actions without making changes.')
    group.add_argument('--non-interactive', action='store_true', help='Run the script without any interactive prompts.')
    args = parser.parse_args()
    return args

# ------------------------ Main Execution ------------------------

def main():
    global CLEANUP_DONE
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    spec_logger, error_logger = setup_logging()
    
    # Register cleanup function on exit and signal interrupts
    atexit.register(cleanup, spec_logger=spec_logger, error_logger=error_logger)
    signal.signal(signal.SIGINT, lambda signum, frame: cleanup(spec_logger, error_logger))
    signal.signal(signal.SIGTERM, lambda signum, frame: cleanup(spec_logger, error_logger))
    
    # Check required commands
    check_required_commands(spec_logger, error_logger)
    
    # Ensure the script is run as root
    ensure_root(spec_logger, error_logger)
    
    # Determine execution mode
    mode_container = {'mode': 'interactive'}
    if args.non_interactive:
        mode = "normal"
    elif args.dry_run:
        mode = "dry"
    else:
        # Interactive mode
        show_interactive_menu(mode_container)
        mode = mode_container['mode']
    
    log_info(f"Starting disk checks in '{mode}' mode.", spec_logger)
    
    # Get list of external disks
    disks = get_external_disks(spec_logger, error_logger)
    
    if not disks:
        log_info("No external disks found to check.", spec_logger)
    else:
        for disk in disks:
            log_info("----------------------------------------", spec_logger)
            log_info(f"Checking {disk}...", spec_logger)
            
            fs_type = get_filesystem(disk, spec_logger, error_logger)
            if fs_type == "unknown":
                log_error(f"Unable to determine filesystem type for {disk}. Skipping verification.", spec_logger, error_logger)
                continue
            
            # Attempt to unmount disk if necessary
            if not unmount_disk(disk, mode, spec_logger, error_logger):
                continue  # Skip verification if unmount failed
            
            # Verify and repair filesystem
            verify_filesystem(disk, fs_type, mode, spec_logger, error_logger)
            
            # Remount disk if it was unmounted
            if disk in UNMOUNTED_DISKS:
                mount_disk(disk, mode, spec_logger, error_logger)
            
            log_info(f"Done with {disk}.", spec_logger)
    
    log_info("----------------------------------------", spec_logger)
    log_info("Disk Check Completed.", spec_logger)
    
    # Append summary to error log
    append_summary(spec_logger, error_logger)
    
    # Indicate that cleanup has been handled
    CLEANUP_DONE = True
    sys.exit(0)

if __name__ == "__main__":
    main()
