#!/bin/bash

################################################################################
# Description:
# This script performs a deep check of all external physical disk drives on a 
# Mac Mini, logs the results, and documents any errors requiring manual 
# intervention in a separate log file. It supports both interactive and 
# non-interactive modes as well as a dry-run option.
################################################################################

# ------------------------------------------------------------------------------
#                               Configuration
# ------------------------------------------------------------------------------
set -o nounset
set -o pipefail
# NOTE: We do NOT use `set -e` so the script can continue despite errors.

# Timestamp for log filenames
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')

# Define the log directory and ensure it exists
LOGDIR="/var/log/disk_checks"
mkdir -p "$LOGDIR" || {
    echo "Failed to create log directory '$LOGDIR'. Exiting." >&2
    exit 1
}

# Define log file paths with timestamp
LOGFILE="$LOGDIR/check-disks-$TIMESTAMP.log"
ERRORLOG="$LOGDIR/errors-$TIMESTAMP.log"

# Array of required commands
REQUIRED_COMMANDS=(
    "diskutil" "grep" "awk" "mkdir" "touch" "tee"
    "date" "read" "echo" "sleep" "cat"
)

# ------------------------------------------------------------------------------
#                               Helper Functions
# ------------------------------------------------------------------------------

# Log an informational message (stdout + log file)
log_info() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO  - $message" \
        | tee -a "$LOGFILE"
}

# Log an error message (stderr + both log files)
log_error() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $message" \
        | tee -a "$ERRORLOG" "$LOGFILE" >&2
}

# Check if a command exists in PATH
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determine filesystem type for a given disk
get_filesystem() {
    local disk="$1"
    # For macOS, "Type (Bundle)" line usually gives the fs type, e.g. "apfs", "hfs", "msdos", etc.
    diskutil info "$disk" 2>/dev/null \
        | grep "Type (Bundle)" \
        | awk -F': ' '{print tolower($2)}' \
        || echo "unknown"
}

# Cleanup function to handle script interruption or normal exit
cleanup() {
    # This variable prevents double-calling cleanup if the script hits multiple signals
    if [ "${CLEANUP_DONE:-}" != "true" ]; then
        log_info "Script interrupted or exiting. Performing cleanup."

        # Attempt to remount any disks that were unmounted by this script
        for disk in "${UNMOUNTED_DISKS[@]}"; do
            log_info "Attempting to remount $disk..."
            if diskutil mountDisk "$disk" >> "$LOGFILE" 2>&1; then
                log_info "$disk remounted successfully."
            else
                log_error "Unable to remount $disk during cleanup. Please remount it manually if needed."
            fi
        done

        # Append final summary if not appended yet
        # (In case the script was interrupted before the normal summary section)
        if ! grep -q "===== Summary of Recommendations =====" "$ERRORLOG" 2>/dev/null; then
            echo "===== Summary of Recommendations =====" >> "$ERRORLOG"
            if [ -s "$ERRORLOG" ]; then
                echo "Some disks encountered issues that require manual intervention." \
                     "Please review the above errors and take appropriate actions." \
                     >> "$ERRORLOG"
            else
                echo "All disk checks completed without errors." >> "$ERRORLOG"
            fi
        fi

        CLEANUP_DONE=true
    fi

    # We exit with 0 so we don’t treat an interrupt as a script failure
    # If you prefer a non-zero exit for interruptions, change to `exit 1`.
    exit 0
}

# Display interactive menu for normal / dry-run / non-interactive
show_menu() {
    echo
    echo "Select an option:"
    echo "1) Run normally"
    echo "2) Dry run (simulate actions without making changes)"
    echo "3) Run non-interactively with default settings"
    echo "4) Exit"
    read -rp "Enter your choice [1-4]: " choice

    case "$choice" in
        1) MODE="normal" ;;
        2) MODE="dry" ;;
        3) MODE="non_interactive" ;;
        4) echo "Exiting."; exit 0 ;;
        *) echo "Invalid choice. Exiting."; exit 1 ;;
    esac
}

# Parse command-line arguments
parse_arguments() {
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --dry-run)
                MODE="dry"
                ;;
            --non-interactive)
                MODE="non_interactive"
                ;;
            --help|-h)
                echo "Usage: $0 [--dry-run] [--non-interactive]"
                echo
                echo "Options:"
                echo "  --dry-run           Simulate actions without making changes."
                echo "  --non-interactive   Run the script without any interactive prompts."
                echo "  --help, -h          Display this help message."
                exit 0
                ;;
            *)
                echo "Unknown parameter passed: $1"
                echo "Use --help to see available options."
                exit 1
                ;;
        esac
        shift
    done
}

# Check for all required commands before proceeding
check_required_commands() {
    local missing_cmds=()

    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command_exists "$cmd"; then
            missing_cmds+=("$cmd")
        fi
    done

    if [ "${#missing_cmds[@]}" -ne 0 ]; then
        for cmd in "${missing_cmds[@]}"; do
            log_error "Required command '$cmd' not found or not executable."
        done
        log_error "Missing required commands: ${missing_cmds[*]}. Exiting."
        exit 1
    fi
}

# Ensure the script is run as root (diskutil repair often requires sudo)
ensure_root() {
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
        echo "This script must be run as root. Please use sudo." \
            | tee -a "$LOGFILE" "$ERRORLOG" >&2
        exit 1
    fi
}

# Initialize the log files with headers if they are empty
initialize_logs() {
    for logfile in "$LOGFILE" "$ERRORLOG"; do
        if [ ! -s "$logfile" ]; then
            echo "===== $(basename "$logfile" | tr '[:lower:]' '[:upper:]') Started at $(date) =====" \
                >> "$logfile"
        fi
    done
}

# Retrieve a list of external physical disks using diskutil
get_external_disks() {
    diskutil list external physical \
        | grep "^/dev/disk" \
        | awk '{print $1}'
}

# Determine if a disk is part of the system or not (quick check)
# This can sometimes exclude external Apple-formatted disks (APFS/HFS+),
# so you may want to refine or remove this check as needed.
is_system_disk() {
    local disk="$1"
    local system_partitions
    system_partitions=$(diskutil list | grep -E "Apple_APFS|Apple_HFS" | awk '{print $1}')
    for sys_disk in $system_partitions; do
        # If disk is a prefix of sys_disk, consider it "system"
        if [[ "$sys_disk" == "$disk"* ]]; then
            return 0
        fi
    done
    return 1
}

# Verify and possibly repair a disk based on filesystem type
verify_filesystem() {
    local disk="$1"
    local fs_type="$2"

    case "$fs_type" in
        # Expand these as needed
        apfs|hfs|hfsplus|msdos|exfat|fat32)
            if [ "$MODE" == "dry" ]; then
                log_info "Dry run: Would verify $disk (filesystem: $fs_type)."
            else
                log_info "Verifying $disk (filesystem: $fs_type)..."
                if verify_output=$(diskutil verifyVolume "$disk" 2>&1); then
                    log_info "$disk verification succeeded."
                else
                    log_error "$disk verification found issues: $verify_output"
                    log_info "Attempting to repair $disk..."
                    if repair_output=$(diskutil repairVolume "$disk" 2>&1); then
                        log_info "$disk repair succeeded."
                    else
                        log_error "Repair failed for $disk. Manual intervention required: $repair_output"
                    fi
                fi
            fi
            ;;
        # We list typical non-Apple or less common FS to catch them gracefully:
        ntfs|ext4|btrfs|xfs|iso9660|smbfs|davfs2|fuseblk|fuse|unknown)
            # On macOS, diskutil typically cannot repair these.
            # We log an error and move on.
            log_error "Unsupported or unknown filesystem '$fs_type' on $disk. Skipping verification."
            ;;
        *)
            # Catch any filesystem that doesn't match the above
            log_error "Unsupported or unknown filesystem '$fs_type' on $disk. Skipping verification."
            ;;
    esac
}

# ------------------------------------------------------------------------------
#                                  Main Logic
# ------------------------------------------------------------------------------

# Prepare to handle unexpected interruptions
trap cleanup INT TERM EXIT

# Initialization
UNMOUNTED_DISKS=()
CLEANUP_DONE=false
MODE="interactive"

# 1) Parse arguments
parse_arguments "$@"

# 2) If still interactive (no mode set from args), show menu
if [ "$MODE" == "interactive" ]; then
    show_menu
fi

# 3) Ensure script is running as root
ensure_root

# 4) Check required commands
check_required_commands

# 5) Initialize logs
initialize_logs

log_info "Starting disk checks in '$MODE' mode."

# Get list of external physical disks
disks=$(get_external_disks)

if [ -z "$disks" ]; then
    log_info "No external disks found to check."
else
    # For each external disk:
    for disk in $disks; do
        log_info "----------------------------------------"
        log_info "Checking $disk..."

        # Safety check: skip system/boot disk
        if is_system_disk "$disk"; then
            log_error "$disk appears to be (or contain) a system disk. Skipping."
            continue
        fi

        # Determine filesystem type
        fs_type=$(get_filesystem "$disk")
        if [ -z "$fs_type" ] || [ "$fs_type" == "unknown" ]; then
            log_error "Unable to determine filesystem type for $disk. Skipping verification."
            continue
        fi
        log_info "Filesystem type for $disk: $fs_type"

        # Check if disk is currently mounted
        mount_status=$(diskutil info "$disk" | grep "^Mounted:" | awk '{print $2}')
        was_mounted=false
        if [[ "$mount_status" == "Yes" ]]; then
            was_mounted=true
            if [ "$MODE" == "dry" ]; then
                log_info "Dry run: Would unmount $disk before verification."
            else
                log_info "$disk is mounted. Attempting to unmount..."
                if unmount_output=$(diskutil unmountDisk "$disk" 2>&1); then
                    log_info "$disk unmounted successfully."
                    # Track unmounted disk for cleanup
                    UNMOUNTED_DISKS+=("$disk")
                else
                    log_error "Unable to unmount $disk. It may be in use. Skipping verification."
                    continue
                fi
            fi
        else
            log_info "$disk is not mounted. Proceeding with verification."
        fi

        # Verify (and possibly repair) the disk
        verify_filesystem "$disk" "$fs_type"

        # If it was mounted before, try remounting
        if [ "$was_mounted" = true ] && [ "$MODE" != "dry" ]; then
            log_info "Attempting to remount $disk..."
            if mount_output=$(diskutil mountDisk "$disk" 2>&1); then
                log_info "$disk remounted successfully."
                # Remove from the UNMOUNTED_DISKS array
                UNMOUNTED_DISKS=("${UNMOUNTED_DISKS[@]/$disk}")
            else
                log_error "Unable to remount $disk. You may need to mount it manually."
            fi
        fi

        log_info "Done with $disk."
    done
fi

log_info "----------------------------------------"
log_info "Disk Check Completed."

# ------------------------------------------------------------------------------
#                            Summary and Finalization
# ------------------------------------------------------------------------------

# Add summary header to the error log
echo "===== Summary of Recommendations =====" >> "$ERRORLOG"

# If there are actual errors (besides the header lines) in ERRORLOG
# we can do a quick search for the word "ERROR"
error_count=$(grep -c "ERROR" "$ERRORLOG" 2>/dev/null || true)

if [ "$error_count" -gt 0 ]; then
    log_info "Some errors were encountered. Please review '$ERRORLOG' for details."
else
    log_info "No errors detected. All disk checks passed successfully."
    # If no real errors, empty the file, then add a minimal summary
    > "$ERRORLOG"
    echo "===== Summary of Recommendations =====" >> "$ERRORLOG"
    echo "All disk checks completed without errors." >> "$ERRORLOG"
fi

# Mark cleanup as done to avoid re-triggering in trap
CLEANUP_DONE=true
log_info "Exiting script now."
exit 0
