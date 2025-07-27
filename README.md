# n8n Release Monitor with ntfy 📦📱

**Ultra-simple n8n release monitoring with ntfy notifications - just one HTTP call!**

## 🚀 What This Does

- **Monitors n8n releases daily** using GitHub Actions (100% free)
- **Detects changes** automatically and intelligently  
- **Sends notifications via ntfy** to your phone/desktop instantly
- **No secrets needed** - ntfy topics are public by design
- **Zero configuration** - works out of the box

## ⚡ Super Quick Start

```bash
# 1. Test it locally
uv run n8n_monitor.py --test-notifications

# 2. Subscribe to notifications (get the ntfy app or visit web)
# iOS/Android: Search "ntfy" in app store, subscribe to "your-topic-name"  
# Web: Visit https://ntfy.sh/your-topic-name

# 3. Test monitoring
uv run n8n_monitor.py --monitor --no-notify

# 4. Deploy to GitHub Actions for daily automation
```

That's it! No webhooks, no API keys, no configuration files.

## 📱 Getting Notifications

### Option 1: ntfy App (Recommended)
1. Install ntfy app from [App Store](https://apps.apple.com/us/app/ntfy/id1625396347) or [Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. Subscribe to your chosen topic name
3. Done! You'll get push notifications instantly

### Option 2: Web Browser
- Visit: https://ntfy.sh/your-topic-name
- Keep tab open to see notifications in real-time

### Option 3: Configure Topic
Set your topic via GitHub repository variables:
- Go to Settings → Secrets and variables → Actions → Variables  
- Add `N8N_NTFY_TOPIC` with your chosen topic name

## 📋 Example Notification

Your phone will receive:
```
🎉 New n8n Release: n8n@1.104.2

📅 Release Date: 2025-07-28

📝 Changes:
• New AI Agent Tool node for multi-agent orchestration
• Built-in Metrics for AI Evaluations

🔍 Release Highlights:
• This release contains core updates, editor improvements...
• New node for enhanced workflow capabilities...

🔗 Full notes: https://docs.n8n.io/release-notes
⏰ 2025-07-28 09:15 UTC
```

## 🤖 GitHub Actions Setup (2 minutes)

1. **Create GitHub repo** and upload `n8n_monitor.py`
2. **Add workflow file**: Copy `.github/workflows/n8n-monitor.yml`  
3. **Done!** No secrets or environment variables needed

The workflow runs daily at 9 AM UTC and automatically commits any changes.

## 🔧 Commands

```bash
# Test notifications
uv run n8n_monitor.py --test-notifications

# Monitor with notifications (production mode)
uv run n8n_monitor.py --monitor

# Monitor without notifications (testing)
uv run n8n_monitor.py --monitor --no-notify

# Get multiple releases
uv run n8n_monitor.py --mode all --limit 5

# One-time check
uv run n8n_monitor.py
```

## 🎯 Smart Features

**Change Detection:**
- New versions: `n8n@1.104.1` → `n8n@1.104.2`
- Content updates: Same version but updated release notes
- First run: Captures baseline data

**Notification Priorities:**
- 🔴 **Priority 5**: Errors (max urgency)
- 🟡 **Priority 4**: New releases (high urgency)  
- 🔵 **Priority 3**: Test notifications (normal)

**Tags:** Notifications include relevant tags (`package`, `n8n`, `test`, `error`)

## 📁 What Gets Created

```
data/
├── latest_release.json    # Current release data
└── release_history.json   # Last 50 releases
```

## ✨ Why ntfy is Perfect for This

**Pros:**
- ✅ **Zero setup** - no accounts, no API keys, no webhooks
- ✅ **Multi-platform** - works on iOS, Android, desktop, web
- ✅ **Instant delivery** - real-time push notifications
- ✅ **Reliable** - built for exactly this use case
- ✅ **Free** - no costs for basic usage
- ✅ **Privacy-friendly** - only message content is sent

**Public Topics:**
- Topics are public by design (anyone can send/receive)
- Use a unique topic name if you want to reduce noise
- No sensitive data is sent (just release information)

## 🛠 Customization

**Change notification topic:**
```python
# In the script, modify this line:
service = NotificationService(topic="my-custom-topic")
```

**Change message format:**
Edit the `send_new_release_notification` method in the script.

**Change schedule:**
Edit the `cron` line in `.github/workflows/n8n-monitor.yml`:
```yaml
- cron: '0 */6 * * *'  # Every 6 hours
- cron: '0 9 * * 1-5'  # Weekdays only
```

## 💰 Total Cost: $0

- GitHub Actions: **FREE**
- ntfy notifications: **FREE** 
- No servers, no subscriptions, no hidden costs

## 🎉 Perfect For

- **Personal projects** - Stay updated on your favorite tools
- **Development teams** - Share release updates instantly  
- **DevOps monitoring** - Add to your notification stack
- **Learning UV** - Great example of single-file scripts with dependencies

**Simple. Effective. Free. 🎯**

## 🔧 Troubleshooting

**GitHub Actions failing with permission errors?**
- The workflow includes `permissions: contents: write` to allow commits
- Ensure Actions are enabled: Settings → Actions → General → "Allow all actions"

**Not receiving notifications?**
- Check that you're subscribed to the correct ntfy topic
- Verify `N8N_NTFY_TOPIC` is set correctly in GitHub Variables
- Test locally: `uv run n8n_monitor.py --test`

**Want to see what's happening?**
- Check the Actions tab in your GitHub repository
- Manual trigger: Actions → "n8n Release Monitor" → "Run workflow"