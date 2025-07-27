#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests>=2.31.0",
#     "beautifulsoup4>=4.12.0", 
#     "lxml>=4.9.0",
# ]
# ///
"""
n8n Release Monitor
Ultra-minimal n8n release monitoring with ntfy notifications.

Usage:
    uv run n8n_monitor.py --monitor        # Monitor with notifications
    uv run n8n_monitor.py --test          # Test notifications
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def send_ntfy(topic, message, title="", priority=3, tags=""):
    """Send ntfy notification"""
    try:
        headers = {"X-Title": title, "X-Priority": str(priority), "X-Tags": tags}
        response = requests.post(f"https://ntfy.sh/{topic}", data=message, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False


def fetch_releases(limit=1):
    """Fetch n8n releases from docs"""
    try:
        response = requests.get("https://docs.n8n.io/release-notes", timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find version headers
        headers = [h for h in soup.find_all('h2') if h.get_text() and 'n8n@' in h.get_text()]
        if not headers:
            return []
        
        releases = []
        for i, header in enumerate(headers[:limit]):
            version = header.get_text().strip().replace('#', '')
            
            # Get content until next version header
            content = []
            current = header.next_sibling
            next_header = headers[i + 1] if i + 1 < len(headers) else None
            
            while current and current != next_header:
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text and 'n8n@' not in text:
                        if current.name in ['ul', 'ol']:
                            content.extend(f"• {li.get_text().strip()}" for li in current.find_all('li'))
                        else:
                            content.append(text)
                current = current.next_sibling
            
            releases.append({
                'version': version,
                'content': content,
                'scraped_at': datetime.now().isoformat()
            })
        
        return releases
    except Exception as e:
        print(f"❌ Failed to fetch releases: {e}")
        return []


def load_data(file_path):
    """Load JSON data from file"""
    try:
        return json.load(open(file_path)) if file_path.exists() else None
    except:
        return None


def save_data(file_path, data):
    """Save JSON data to file"""
    try:
        file_path.parent.mkdir(exist_ok=True)
        json.dump(data, open(file_path, 'w'), indent=2, ensure_ascii=False)
        return True
    except:
        return False


def detect_changes(current, previous):
    """Compare releases and detect changes"""
    if not previous:
        return True, "First run"
    
    curr_ver = current.get('version', '')
    prev_ver = previous.get('version', '')
    
    if curr_ver != prev_ver:
        return True, f"New version: {prev_ver} → {curr_ver}"
    
    if current.get('content') != previous.get('content'):
        return True, f"Content updated for {curr_ver}"
    
    return False, "No changes"


def format_notification(release, change_reason):
    """Format release data for notification"""
    version = release.get('version', 'Unknown')
    content = release.get('content', [])
    
    # Extract release date
    date_info = ""
    for item in content:
        if "Release date:" in item:
            date_info = f"\n📅 {item.split('Release date:')[-1].strip()}"
            break
    
    # Get highlights (first 2 non-date items)
    highlights = []
    for item in content[:4]:
        if item and "Release date:" not in item and len(item.strip()) > 10:
            clean_item = item.replace('\n', ' ').strip()
            if len(clean_item) > 80:
                clean_item = clean_item[:77] + "..."
            highlights.append(f"• {clean_item}")
            if len(highlights) >= 2:
                break
    
    message = f"🎉 New n8n Release: {version}{date_info}\n"
    if highlights:
        message += f"\n🔍 Highlights:\n" + "\n".join(highlights) + "\n"
    message += f"\n🔗 https://docs.n8n.io/release-notes\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    
    return message


def main():
    # Environment variable defaults
    default_topic = os.getenv('N8N_NTFY_TOPIC', 'jksr_notifications')
    default_data_dir = os.getenv('N8N_DATA_DIR', 'data')
    env_no_notify = os.getenv('N8N_NO_NOTIFY', '').lower() in ('1', 'true', 'yes')
    
    parser = argparse.ArgumentParser(description='n8n Release Monitor')
    parser.add_argument('--monitor', action='store_true', help='Monitor mode with change detection')
    parser.add_argument('--test', action='store_true', help='Send test notification')
    parser.add_argument('--no-notify', action='store_true', help='Disable notifications (env: N8N_NO_NOTIFY)')
    parser.add_argument('--topic', default=default_topic, help=f'ntfy topic (env: N8N_NTFY_TOPIC, default: {default_topic})')
    parser.add_argument('--data-dir', default=default_data_dir, help=f'Data directory (env: N8N_DATA_DIR, default: {default_data_dir})')
    
    args = parser.parse_args()
    
    # Apply environment variable for no-notify if not overridden by CLI
    if env_no_notify and not args.no_notify:
        args.no_notify = True
    
    # Test mode
    if args.test:
        print("🧪 Testing ntfy notifications...")
        message = f"Test from n8n monitor\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        success = send_ntfy(args.topic, message, "n8n Monitor Test", 3, "test")
        print(f"{'✅ Success' if success else '❌ Failed'}")
        if success:
            print(f"Check: https://ntfy.sh/{args.topic}")
        return 0 if success else 1
    
    # Monitor mode
    if args.monitor:
        print("🔍 Fetching n8n releases...")
        
        # Fetch current release
        releases = fetch_releases(1)
        if not releases:
            if not args.no_notify:
                send_ntfy(args.topic, "Failed to fetch n8n releases", "n8n Monitor Error", 5, "error")
            return 1
        
        current = releases[0]
        data_dir = Path(args.data_dir)
        latest_file = data_dir / "latest.json"
        
        # Load previous data
        previous = load_data(latest_file)
        
        # Check for changes
        has_changes, reason = detect_changes(current, previous)
        
        if has_changes:
            print(f"✅ Changes detected: {reason}")
            
            # Save new data
            if save_data(latest_file, current):
                print(f"💾 Data saved to {latest_file}")
            
            # Send notification
            if not args.no_notify:
                message = format_notification(current, reason)
                success = send_ntfy(args.topic, message, f"New n8n Release: {current['version']}", 4, "package,n8n")
                print(f"📤 Notification: {'✅ Sent' if success else '❌ Failed'}")
            
            # Display release info
            print(f"\n🎉 {current['version']}")
            for item in current.get('content', [])[:3]:
                if item.strip():
                    print(f"  {item[:100]}{'...' if len(item) > 100 else ''}")
        else:
            print(f"ℹ️ {reason}")
        
        return 0
    
    # Default: just fetch and display latest
    releases = fetch_releases(1)
    if releases:
        release = releases[0]
        print(f"Latest: {release['version']}")
        for item in release.get('content', [])[:2]:
            if item.strip():
                print(f"  {item[:80]}{'...' if len(item) > 80 else ''}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())