import os
import time
import requests
from pathlib import Path
from datetime import datetime, timezone

FEED_URL = os.environ["GTFS_RT_URL"]
INTERVAL = int(os.environ["FETCH_INTERVAL_SECONDS"])
DATA_DIR = Path(os.environ["DATA_DIR"])

def fetch_feed(url: str, dest_dir: Path) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    filename = f"{timestamp}.pb"
    filepath = dest_dir / filename
    filepath.write_bytes(response.content)
    
    print(f"[{timestamp}] Saved {len(response.content)} bytes → {filepath}")

def main():
    print(f"Starting fetcher — URL: {FEED_URL}")
    print(f"Saving to: {DATA_DIR}")
    print(f"Interval: {INTERVAL}s")
    
    while True:
        try:
            fetch_feed(FEED_URL, DATA_DIR)
        except requests.RequestException as e:
            print(f"[ERROR] Network problem: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
        
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
    