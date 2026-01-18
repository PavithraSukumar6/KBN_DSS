import os
import time
import shutil
import requests
import sys

# Configuration
WATCH_DIR = os.path.join(os.getcwd(), "watch_input")
PROCESSED_DIR = os.path.join(os.getcwd(), "watch_processed")
ERROR_DIR = os.path.join(os.getcwd(), "watch_errors")
SERVER_URL = "http://localhost:5000/upload"
POLL_INTERVAL_SECONDS = 5
UPLOADER_ID = "WatchBot"

def ensure_dirs():
    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(ERROR_DIR, exist_ok=True)

def process_file(filename):
    filepath = os.path.join(WATCH_DIR, filename)
    
    # Wait for file to be stable (in case it's still copying)
    initial_size = -1
    retries = 5
    while retries > 0:
        try:
            current_size = os.path.getsize(filepath)
            if current_size == initial_size:
                break
            initial_size = current_size
            time.sleep(1)
            retries -= 1
        except OSError:
            time.sleep(1)
            retries -= 1
            
    print(f"Processing {filename}...")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {'uploader_id': UPLOADER_ID, 'category': 'Invoice'} # Default or Auto-Detect? User didn't specify. 'Invoice' triggers the regex logic best.
            
            response = requests.post(SERVER_URL, files=files, data=data)
            
            if response.status_code == 200:
                print(f"Successfully uploaded {filename}. Moving to processed.")
                shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
            else:
                print(f"Failed to upload {filename}. Status: {response.status_code}. Response: {response.text}")
                shutil.move(filepath, os.path.join(ERROR_DIR, filename))

    except Exception as e:
        print(f"Exception processing {filename}: {e}")
        try:
            shutil.move(filepath, os.path.join(ERROR_DIR, filename))
        except:
            pass

def main():
    ensure_dirs()
    print(f"Monitoring {WATCH_DIR}...")
    print(f"Server URL: {SERVER_URL}")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            files = [f for f in os.listdir(WATCH_DIR) if os.path.isfile(os.path.join(WATCH_DIR, f))]
            for f in files:
                # Ignore hidden files
                if f.startswith('.'): continue
                process_file(f)
            
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopping Watch Folder Service.")

if __name__ == "__main__":
    main()
