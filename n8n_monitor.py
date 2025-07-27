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
n8n Release Monitor - Single File Edition
A complete n8n release monitoring system with change detection and notifications.

Usage:
    uv run n8n_monitor.py --monitor                    # Monitor with notifications
    uv run n8n_monitor.py --monitor --no-notify        # Monitor without notifications  
    uv run n8n_monitor.py --test-notifications         # Test notification setup
    uv run n8n_monitor.py --mode all --limit 5         # Get 5 latest releases
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


class NotificationService:
    """Simple ntfy notification service"""
    
    def __init__(self, topic: str = "jksr_notifications"):
        self.topic = topic
        self.base_url = "https://ntfy.sh"
        self.enabled = True
        print(f"📱 ntfy notifications enabled (topic: {topic})")

    def _send_ntfy(self, message: str, title: str = "", priority: int = 3, tags: str = ""):
        """Send notification via ntfy"""
        if not self.enabled:
            return False
            
        url = f"{self.base_url}/{self.topic}"
        headers = {}
        
        if title:
            headers["X-Title"] = title
        if priority != 3:
            headers["X-Priority"] = str(priority)
        if tags:
            headers["X-Tags"] = tags
            
        try:
            response = requests.post(url, data=message, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send ntfy notification: {e}")
            return False

    def send_new_release_notification(self, release_data: Dict, changes_summary: str = ""):
        """Send notification about a new n8n release"""
        
        version = release_data.get('version', 'Unknown')
        content = release_data.get('content', [])
        
        # Create notification title and body
        title = f"New n8n Release: {version}"
        
        body_parts = [
            f"🎉 A new n8n release is available: {version}",
            "",
        ]
        
        # Add release date if available
        for item in content:
            if "Release date:" in item:
                date_part = item.split("Release date:")[-1].strip()
                body_parts.append(f"📅 Release Date: {date_part}")
                break
        
        # Add changes summary if provided
        if changes_summary:
            body_parts.extend([
                "",
                "📝 Changes:",
                changes_summary
            ])
        
        # Add key release highlights
        if content:
            body_parts.extend([
                "",
                "🔍 Release Highlights:"
            ])
            
            for item in content[:2]:  # Show first 2 items to keep it concise
                if item.strip() and "Release date:" not in item:
                    # Clean up the item and truncate if too long
                    clean_item = item.replace('\n', ' ').strip()
                    if len(clean_item) > 100:
                        clean_item = clean_item[:97] + "..."
                    body_parts.append(f"• {clean_item}")
        
        body_parts.extend([
            "",
            "🔗 Full notes: https://docs.n8n.io/release-notes",
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        ])
        
        message = "\n".join(body_parts)
        
        # Send notification with high priority for new releases
        return self._send_ntfy(message, title=title, priority=4, tags="package,n8n")

    def send_error_notification(self, error_message: str):
        """Send notification about crawler errors"""
        
        title = "n8n Monitor Error"
        message = f"""❌ The n8n release monitor encountered an error:

Error: {error_message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check the logs for more details."""
        
        # Send with max priority for errors
        return self._send_ntfy(message, title=title, priority=5, tags="warning,error")

    def send_test_notification(self):
        """Send a test notification to verify setup"""
        
        title = "n8n Monitor Test"
        message = f"""🧪 This is a test notification from the n8n release monitor.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Topic: {self.topic}

If you receive this message, your notification setup is working correctly! 🎉"""
        
        return self._send_ntfy(message, title=title, priority=3, tags="test")


class N8NReleaseCrawler:
    """n8n release notes crawler with change detection"""
    
    def __init__(self, data_dir: str = "data"):
        self.base_url = "https://docs.n8n.io/release-notes"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.latest_file = self.data_dir / "latest_release.json"
        self.history_file = self.data_dir / "release_history.json"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.notification_service = NotificationService()

    def fetch_page(self):
        """Fetch the release notes page"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def parse_all_releases(self, html_content, limit=None):
        """Parse the HTML content to extract all release notes"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all version headers (h2 tags that contain 'n8n@')
        version_headers = soup.find_all('h2', string=lambda text: text and 'n8n@' in text)
        
        # If that doesn't work, try a more flexible approach
        if not version_headers:
            all_h2 = soup.find_all('h2')
            version_headers = [h for h in all_h2 if h.get_text() and 'n8n@' in h.get_text()]
        
        if not version_headers:
            print("Could not find any version headers")
            return []

        # Apply limit if specified
        if limit:
            version_headers = version_headers[:limit]

        releases = []
        scraped_at = datetime.now().isoformat()

        for i, header in enumerate(version_headers):
            version_text = header.get_text().strip().replace('#', '')
            
            # Find the next version header to know where this version's content ends
            next_header = version_headers[i + 1] if i + 1 < len(version_headers) else None
            
            # Extract content for this specific version
            content_elements = []
            current = header.next_sibling

            while current:
                # Stop if we hit the next version header
                if next_header and current == next_header:
                    break
                if current and hasattr(current, 'name') and current.name == 'h2':
                    if current.get_text() and 'n8n@' in current.get_text() and current != header:
                        break
                
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text:
                        if current.name in ['ul', 'ol']:
                            for li in current.find_all('li'):
                                content_elements.append(f"• {li.get_text().strip()}")
                        else:
                            content_elements.append(text)
                
                current = current.next_sibling

            # Also use find_next_sibling to get structured content until next version
            next_element = header.find_next_sibling()
            processed_elements = set()
            
            while next_element:
                # Stop if we hit the next version header
                if next_header and next_element == next_header:
                    break
                if next_element.name == 'h2' and 'n8n@' in next_element.get_text() and next_element != header:
                    break
                    
                element_id = id(next_element)
                if element_id not in processed_elements:
                    processed_elements.add(element_id)
                    
                    if next_element.name in ['ul', 'ol']:
                        for li in next_element.find_all('li'):
                            list_item = f"• {li.get_text().strip()}"
                            if list_item not in content_elements:
                                content_elements.append(list_item)
                    elif next_element.get_text().strip():
                        text = next_element.get_text().strip()
                        if text not in content_elements:
                            content_elements.append(text)
                
                next_element = next_element.find_next_sibling()

            # Clean up content - remove duplicates while preserving order
            cleaned_content = []
            seen = set()
            for item in content_elements:
                if item and item not in seen:
                    cleaned_content.append(item)
                    seen.add(item)

            releases.append({
                'version': version_text,
                'content': cleaned_content,
                'scraped_at': scraped_at
            })

        return releases

    def parse_latest_release(self, html_content):
        """Parse the HTML content to extract just the latest release note"""
        all_releases = self.parse_all_releases(html_content, limit=1)
        return all_releases[0] if all_releases else None

    def load_previous_data(self) -> Optional[Dict]:
        """Load the previous release data for comparison"""
        try:
            if self.latest_file.exists():
                with open(self.latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading previous data: {e}")
        return None

    def save_release_data(self, release_data: Dict):
        """Save release data to files"""
        try:
            # Save latest release
            with open(self.latest_file, 'w', encoding='utf-8') as f:
                json.dump(release_data, f, indent=2, ensure_ascii=False)
            
            # Update history
            history = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except:
                    history = []
            
            # Add to history if it's a new version
            if not history or history[0].get('version') != release_data.get('version'):
                history.insert(0, release_data)
                
                # Keep only last 50 releases to prevent file from growing too large
                history = history[:50]
                
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Data saved to {self.data_dir}")
            
        except Exception as e:
            print(f"Error saving data: {e}")

    def detect_changes(self, current_release: Dict, previous_release: Optional[Dict]) -> Tuple[bool, str]:
        """Detect changes between current and previous release data"""
        
        if not previous_release:
            return True, "First time running - no previous data to compare"
        
        current_version = current_release.get('version', '')
        previous_version = previous_release.get('version', '')
        
        # Check if version changed
        if current_version != previous_version:
            return True, f"New version detected: {previous_version} → {current_version}"
        
        # Check if content changed (same version but updated content)
        current_content = current_release.get('content', [])
        previous_content = previous_release.get('content', [])
        
        if current_content != previous_content:
            return True, f"Content updated for version {current_version}"
        
        return False, "No changes detected"

    def generate_diff_summary(self, current_release: Dict, previous_release: Optional[Dict]) -> str:
        """Generate a human-readable summary of changes"""
        
        if not previous_release:
            return "Initial release data captured"
        
        current_version = current_release.get('version', '')
        previous_version = previous_release.get('version', '')
        
        if current_version != previous_version:
            # New version - highlight what's new
            content = current_release.get('content', [])
            
            summary_parts = []
            for item in content[:3]:  # First 3 items
                if item and "Release date:" not in item:
                    clean_item = item.replace('\n', ' ').strip()
                    if len(clean_item) > 80:
                        clean_item = clean_item[:77] + "..."
                    summary_parts.append(f"• {clean_item}")
            
            return "\n".join(summary_parts) if summary_parts else "No detailed changes available"
        else:
            # Same version, content updated
            return f"Release notes updated for {current_version}"

    def display_release(self, release_data):
        """Display a single release data in a formatted way"""
        if not release_data:
            print("No release data to display")
            return

        print("=" * 60)
        print(f"N8N RELEASE: {release_data['version']}")
        print("=" * 60)
        print(f"Scraped at: {release_data['scraped_at']}")
        print()
        
        if release_data['content']:
            print("RELEASE DETAILS:")
            print("-" * 40)
            for item in release_data['content']:
                if item.strip():
                    print(item)
                    print()
        else:
            print("No detailed content found for this release.")
        
        print("=" * 60)

    def display_all_releases(self, releases_data):
        """Display all releases data in a formatted way"""
        if not releases_data:
            print("No releases data to display")
            return

        print(f"Found {len(releases_data)} releases")
        print("=" * 80)
        
        for i, release in enumerate(releases_data):
            print(f"RELEASE {i+1}/{len(releases_data)}: {release['version']}")
            print("-" * 50)
            
            if release['content']:
                for item in release['content']:
                    if item.strip():
                        print(f"  {item}")
                print()
            else:
                print("  No detailed content found for this release.")
                print()
        
        print("=" * 80)

    def save_to_json(self, data, filename):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to file: {e}")

    def run(self, mode="latest", limit=None, notify=True, monitor=False):
        """Main execution method with change detection and notifications"""
        print("🔍 Fetching n8n release notes...")
        
        try:
            html_content = self.fetch_page()
            if not html_content:
                error_msg = "Failed to fetch release notes page"
                if notify:
                    self.notification_service.send_error_notification(error_msg)
                return False

            if mode == "all":
                print(f"📋 Parsing all releases{f' (limit: {limit})' if limit else ''}...")
                all_releases = self.parse_all_releases(html_content, limit=limit)
                
                if all_releases:
                    self.display_all_releases(all_releases)
                    filename = f"n8n_releases{f'_top{limit}' if limit else '_all'}.json"
                    self.save_to_json(all_releases, filename)
                    return True
                else:
                    error_msg = "Failed to extract release information"
                    if notify:
                        self.notification_service.send_error_notification(error_msg)
                    return False
            else:
                # Monitor mode with change detection
                print("📋 Parsing latest release...")
                current_release = self.parse_latest_release(html_content)
                
                if not current_release:
                    error_msg = "Failed to extract latest release information"
                    if notify:
                        self.notification_service.send_error_notification(error_msg)
                    return False

                if monitor:
                    # Load previous data for comparison
                    print("🔍 Checking for changes...")
                    previous_release = self.load_previous_data()
                    
                    # Detect changes
                    has_changes, change_reason = self.detect_changes(current_release, previous_release)
                    
                    if has_changes:
                        print(f"✅ Changes detected: {change_reason}")
                        
                        # Generate diff summary
                        diff_summary = self.generate_diff_summary(current_release, previous_release)
                        
                        # Save new data
                        self.save_release_data(current_release)
                        
                        # Send notification
                        if notify:
                            print("📤 Sending notification...")
                            success = self.notification_service.send_new_release_notification(
                                current_release, 
                                diff_summary
                            )
                            if success:
                                print("✅ Notification sent successfully")
                            else:
                                print("❌ Failed to send notification")
                        
                        # Display changes
                        self.display_release(current_release)
                        print("\n" + "="*60)
                        print("CHANGE SUMMARY")
                        print("="*60)
                        print(f"Reason: {change_reason}")
                        print(f"Details:\n{diff_summary}")
                        print("="*60)
                        
                        return True
                    else:
                        print(f"ℹ️  No changes detected: {change_reason}")
                        return True
                else:
                    # Regular mode - just display and save
                    self.display_release(current_release)
                    self.save_to_json(current_release, "latest_n8n_release.json")
                    return True
                    
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            if notify:
                self.notification_service.send_error_notification(error_msg)
            return False


def test_notifications():
    """Test function to verify notification setup"""
    print("Testing ntfy notification service...")
    
    service = NotificationService()
    success = service.send_test_notification()
    print(f"Test notification sent: {'✓ Success' if success else '❌ Failed'}")
    
    if success:
        print(f"Check your ntfy app or https://ntfy.sh/{service.topic} for the test message!")
    
    return success


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='n8n Release Monitor - Single File Edition')
    parser.add_argument('--mode', choices=['latest', 'all'], default='latest',
                       help='Scrape latest release only or all releases')
    parser.add_argument('--limit', type=int, 
                       help='Limit number of releases to scrape (only for --mode all)')
    parser.add_argument('--monitor', action='store_true',
                       help='Enable change detection and monitoring mode')
    parser.add_argument('--no-notify', action='store_true',
                       help='Disable notifications (useful for testing)')
    parser.add_argument('--test-notifications', action='store_true',
                       help='Send a test notification and exit')
    parser.add_argument('--data-dir', default='data',
                       help='Directory to store data files (default: data)')
    
    args = parser.parse_args()
    
    # Handle test notifications
    if args.test_notifications:
        success = test_notifications()
        sys.exit(0 if success else 1)
    
    crawler = N8NReleaseCrawler(data_dir=args.data_dir)
    success = crawler.run(
        mode=args.mode, 
        limit=args.limit,
        notify=not args.no_notify,
        monitor=args.monitor
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()