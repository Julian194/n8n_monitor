# Deploy in 60 Seconds ⚡

## Files Needed (Just 2!)

```
your-repo/
├── n8n_monitor.py                    # ← Complete monitoring system (one file!)
└── .github/workflows/n8n-monitor.yml # ← GitHub Actions workflow  
```

## Steps

### 1. Get Notifications Ready (30 seconds)
- **Phone**: Install ntfy app, subscribe to your chosen topic
- **Web**: Open https://ntfy.sh/your-topic-name in a tab

### 2. Deploy (30 seconds)  
1. Create GitHub repo
2. Upload the 2 files above
3. **Enable Actions** (if not already enabled)
   - Go to Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected
4. **Optional**: Configure custom topic
   - Go to Settings → Secrets and variables → Actions → Variables
   - Add `N8N_NTFY_TOPIC` with your custom topic name
5. Done!

**No secrets. Minimal configuration via GitHub Variables.**

### 3. Test (Optional)
```bash
# Test locally first
uv run n8n_monitor.py --test-notifications
```

Check your phone/web for the test notification!

## What Happens Next

- **Runs daily at 9 AM UTC** automatically
- **Monitors n8n releases** and detects changes
- **Sends notifications** to your phone when new releases are found
- **Commits data** to your repo for history tracking

## Configure via GitHub Variables

Available environment variables you can set in GitHub:

- `N8N_NTFY_TOPIC` - Custom ntfy topic (default: `n8n_releases`)
- `N8N_DATA_DIR` - Data directory (default: `data`)  
- `N8N_NO_NOTIFY` - Disable notifications (`true`/`false`)

Set these in: **Settings → Secrets and variables → Actions → Variables**

## That's It! 

**60 seconds. 2 files. Zero configuration. 🚀**

The power of UV single-file scripts + ntfy + GitHub Actions = instant deployment!