# Deploy in 60 Seconds ⚡

## Files Needed (Just 2!)

```
your-repo/
├── n8n_monitor.py                    # ← Complete monitoring system (one file!)
└── .github/workflows/n8n-monitor.yml # ← GitHub Actions workflow  
```

## Steps

### 1. Get Notifications Ready (30 seconds)
- **Phone**: Install ntfy app, subscribe to `jksr-notification`
- **Web**: Open https://ntfy.sh/jksr-notification in a tab

### 2. Deploy (30 seconds)  
1. Create GitHub repo
2. Upload the 2 files above
3. Done!

**No secrets. No configuration. No environment variables.**

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

## Customize Topic (Optional)

Don't want to share the `jksr-notification` topic? 

Edit line 36 in `n8n_monitor.py`:
```python
def __init__(self, topic: str = "your-unique-topic-name"):
```

Then subscribe to your custom topic instead.

## That's It! 

**60 seconds. 2 files. Zero configuration. 🚀**

The power of UV single-file scripts + ntfy + GitHub Actions = instant deployment!