#!/home/sb4/venv/bin/python3.11
"""
Raspberry Pi 5 File Management Script
- Deletes specified files from a target folder
- Downloads files from GitHub repository
- Logs completion to a text file
- Automatically retries on failure with configurable delay
"""

import os
import sys
import requests
import datetime
import time
from pathlib import Path

# Configuration - Modify these variables as needed
CONFIG = {
    # Local folder where files should be deleted from
    'delete_folder': '/home/sb4/MagicMirror/modules/MMM-Planefinder',
    
    # Files to delete (just filenames)
    'files_to_delete': [
        'aircraft.csv',
        'airports.csv', 
        'airlines.csv'
    ],
    
    # GitHub repository information
    'github_user': 'kds54',           # Replace with GitHub username
    'github_repo': 'MMM-Planefinder',    # Replace with repository name
    'github_branch': 'main',             # Branch to download from
    
    # Files to download from GitHub (with their paths in the repo)
    'files_to_download': [
        'aircraft.csv',
        'airports.csv', 
        'airlines.csv'   # Path in the GitHub repo
    ],
    
    # Local folder where downloaded files should be placed
    'download_folder': '/home/sb4/MagicMirror/modules/MMM-Planefinder',
    
    # Log file path
    'log_file': '/home/sb4/venv/FileManager/FileManager_Log.txt',
    
    # Retry configuration
    'max_retries': 3,           # Maximum number of retry attempts
    'retry_delay_minutes': 2,   # Minutes to wait between retries
}

def ensure_directory_exists(directory_path):
    """Create directory if it doesn't exist."""
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def delete_files():
    """Delete specified files from the target folder."""
    deleted_files = []
    errors = []
    
    for filename in CONFIG['files_to_delete']:
        file_path = os.path.join(CONFIG['delete_folder'], filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(filename)
                print(f"[OK] Deleted: {filename}")
            else:
                print(f"[WARN] File not found (skipping): {filename}")
        except Exception as e:
            error_msg = f"Error deleting {filename}: {str(e)}"
            errors.append(error_msg)
            print(f"[ERROR] {error_msg}")
    
    return deleted_files, errors

def download_file_from_github(file_path, local_filename=None):
    """Download a single file from GitHub repository."""
    if local_filename is None:
        local_filename = os.path.basename(file_path)
    
    # Construct GitHub raw URL
    url = f"https://raw.githubusercontent.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/{CONFIG['github_branch']}/{file_path}"
    
    try:
        print(f"Downloading: {file_path}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Save file to download folder
        local_path = os.path.join(CONFIG['download_folder'], local_filename)
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"[OK] Downloaded: {local_filename}")
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error downloading {file_path}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg

def download_github_files():
    """Download all specified files from GitHub."""
    downloaded_files = []
    errors = []
    
    # Ensure download directory exists
    ensure_directory_exists(CONFIG['download_folder'])
    
    for file_path in CONFIG['files_to_download']:
        success, error = download_file_from_github(file_path)
        if success:
            downloaded_files.append(os.path.basename(file_path))
        else:
            errors.append(error)
    
    return downloaded_files, errors

def log_completion(deleted_files, downloaded_files, errors, attempt_number=1):
    """Write completion entry to log file (overwrites existing content)."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    attempt_text = f" (Attempt {attempt_number})" if attempt_number > 1 else ""
    
    log_entry = f"""{'='*60}
File Management Script Execution{attempt_text}
Timestamp: {timestamp}
{'='*60}

DELETED FILES ({len(deleted_files)}):
{chr(10).join(f"  - {f}" for f in deleted_files) if deleted_files else "  None"}

DOWNLOADED FILES ({len(downloaded_files)}):
{chr(10).join(f"  - {f}" for f in downloaded_files) if downloaded_files else "  None"}

ERRORS ({len(errors)}):
{chr(10).join(f"  - {e}" for e in errors) if errors else "  None"}

Status: {"COMPLETED WITH ERRORS" if errors else "COMPLETED SUCCESSFULLY"}
{'='*60}
"""
    
    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(CONFIG['log_file'])
        if log_dir:
            ensure_directory_exists(log_dir)
        
        # Use 'w' mode to overwrite the file instead of 'a' to append
        with open(CONFIG['log_file'], 'w', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"[OK] Log entry written to: {CONFIG['log_file']}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error writing to log file: {str(e)}")
        return False

def run_file_management():
    """Execute the file management operations once."""
    all_errors = []
    
    # Step 1: Delete files
    print("Step 1: Deleting files...")
    deleted_files, delete_errors = delete_files()
    all_errors.extend(delete_errors)
    
    # Step 2: Download files from GitHub
    print("Step 2: Downloading files from GitHub...")
    downloaded_files, download_errors = download_github_files()
    all_errors.extend(download_errors)
    
    return deleted_files, downloaded_files, all_errors

def main():
    """Main execution function with retry logic."""
    print("Starting Raspberry Pi File Management Script")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Max retries: {CONFIG['max_retries']}")
    print(f"Retry delay: {CONFIG['retry_delay_minutes']} minutes")
    print("-" * 60)
    
    for attempt in range(1, CONFIG['max_retries'] + 1):
        print(f"\n{'='*20} ATTEMPT {attempt} {'='*20}")
        
        try:
            # Execute file management operations
            deleted_files, downloaded_files, all_errors = run_file_management()
            
            # Log the attempt
            print(f"\nStep 3: Writing to log file...")
            log_success = log_completion(deleted_files, downloaded_files, all_errors, attempt)
            
            # Check if successful
            if not all_errors:
                # Success! Print summary and exit
                print("\n" + "="*60)
                print("EXECUTION SUMMARY - SUCCESS")
                print("="*60)
                print(f"Attempt: {attempt}")
                print(f"Files deleted: {len(deleted_files)}")
                print(f"Files downloaded: {len(downloaded_files)}")
                print(f"Errors encountered: {len(all_errors)}")
                print(f"Log file updated: {'Yes' if log_success else 'No'}")
                print("\n[OK] Script completed successfully!")
                sys.exit(0)
            
            else:
                # Has errors, decide whether to retry
                print("\n" + "="*60)
                print(f"ATTEMPT {attempt} SUMMARY - FAILED")
                print("="*60)
                print(f"Files deleted: {len(deleted_files)}")
                print(f"Files downloaded: {len(downloaded_files)}")
                print(f"Errors encountered: {len(all_errors)}")
                print(f"Log file updated: {'Yes' if log_success else 'No'}")
                
                if attempt < CONFIG['max_retries']:
                    delay_seconds = CONFIG['retry_delay_minutes'] * 60
                    print(f"\n[WARN] Attempt {attempt} failed with errors. Retrying in {CONFIG['retry_delay_minutes']} minutes...")
                    print("Errors encountered:")
                    for error in all_errors:
                        print(f"  - {error}")
                    print(f"\nWaiting {CONFIG['retry_delay_minutes']} minutes before retry...")
                    time.sleep(delay_seconds)
                else:
                    # Final attempt failed
                    print(f"\n[ERROR] All {CONFIG['max_retries']} attempts failed. Script execution terminated.")
                    print("Final errors encountered:")
                    for error in all_errors:
                        print(f"  - {error}")
                    sys.exit(1)
        
        except Exception as e:
            print(f"\n[ERROR] Unexpected error in attempt {attempt}: {str(e)}")
            if attempt < CONFIG['max_retries']:
                delay_seconds = CONFIG['retry_delay_minutes'] * 60
                print(f"Retrying in {CONFIG['retry_delay_minutes']} minutes...")
                time.sleep(delay_seconds)
            else:
                print(f"[ERROR] All {CONFIG['max_retries']} attempts failed due to unexpected errors.")
                sys.exit(1)
    
    # This should never be reached, but just in case
    print("[ERROR] Unexpected end of retry loop")
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)