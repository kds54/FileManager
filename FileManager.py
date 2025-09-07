#!/home/spare/venv/bin/python3
"""
Raspberry Pi 5 File Management Script
- Deletes specified files from a target folder
- Downloads files from GitHub repository
- Logs completion to a text file
"""

import os
import sys
import requests
import datetime
from pathlib import Path

# Configuration - Modify these variables as needed
CONFIG = {
    # Local folder where files should be deleted from
    'delete_folder': '/home/spare/MagicMirror/modules/MMM-Planefinder',
    
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
    'download_folder': '/home/spare/MagicMirror/modules/MMM-Planefinder',
    
    # Log file path
    'log_file': '/home/spare/venv/FileManager/FileManager_Log.txt'
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
                print(f"✓ Deleted: {filename}")
            else:
                print(f"⚠ File not found (skipping): {filename}")
        except Exception as e:
            error_msg = f"Error deleting {filename}: {str(e)}"
            errors.append(error_msg)
            print(f"✗ {error_msg}")
    
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
        
        print(f"✓ Downloaded: {local_filename}")
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error downloading {file_path}: {str(e)}"
        print(f"✗ {error_msg}")
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

def log_completion(deleted_files, downloaded_files, errors):
    """Write completion entry to log file (overwrites existing content)."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"""{'='*60}
File Management Script Execution
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
        
        print(f"✓ Log entry written to: {CONFIG['log_file']}")
        return True
        
    except Exception as e:
        print(f"✗ Error writing to log file: {str(e)}")
        return False

def main():
    """Main execution function."""
    print("🚀 Starting Raspberry Pi File Management Script")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    all_errors = []
    
    # Step 1: Delete files
    print("\n📁 Step 1: Deleting files...")
    deleted_files, delete_errors = delete_files()
    all_errors.extend(delete_errors)
    
    # Step 2: Download files from GitHub
    print("\n🌐 Step 2: Downloading files from GitHub...")
    downloaded_files, download_errors = download_github_files()
    all_errors.extend(download_errors)
    
    # Step 3: Log completion
    print("\n📝 Step 3: Writing to log file...")
    log_success = log_completion(deleted_files, downloaded_files, all_errors)
    
    # Summary
    print("\n" + "="*60)
    print("📊 EXECUTION SUMMARY")
    print("="*60)
    print(f"Files deleted: {len(deleted_files)}")
    print(f"Files downloaded: {len(downloaded_files)}")
    print(f"Errors encountered: {len(all_errors)}")
    print(f"Log file updated: {'Yes' if log_success else 'No'}")
    
    if all_errors:
        print("\n⚠ Script completed with errors. Check log file for details.")
        sys.exit(1)
    else:
        print("\n✅ Script completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        sys.exit(1)