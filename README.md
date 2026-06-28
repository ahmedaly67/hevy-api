# Hevy API Client

Reverse-engineered private API client + Vercel proxy for the [Hevy](https://hevy.com) workout tracker. Auto-refreshes tokens every 10 minutes via GitHub Actions. **$0 cost.**

## What this gives you

A live API endpoint that serves your Hevy workout data — usable from any website, dashboard, or app. The GitHub Action keeps it alive by refreshing tokens automatically.

## Quick Start

```bash
git clone https://github.com/ahmedaly67/hevy-api.git
cd hevy-api
```

Then follow **[SETUP.md](SETUP.md)** — a 6-step guide covering:

1. Install dependencies
2. Test locally with Python
3. Deploy to **your own** Vercel account
4. Set up GitHub repo with your own secrets
5. Enable auto-refresh (GitHub Actions every 10 min)
6. Use the API from your dashboard

**Each person deploys to their own Vercel account with their own Hevy login.** No shared credentials.

## API Endpoints

Once deployed, your API will have these endpoints:

| `?path=` | Extra params | Returns |
|-----------|-------------|---------|
| `me` | — | Your Hevy account |
| `profile` | `&username=allstar` | Any user's profile |
| `workout` | `&shortId=xxx` | Full workout (sets, reps, weights) |
| `users` | — | Recommended users |
| `workouts` | — | Feed |
| `routines` | — | Your routines |
| `health` | — | Status check |

## Usage

```javascript
fetch('https://YOUR-DEPLOYMENT.vercel.app/api/hevy?_path=profile&username=allstar')
  .then(r => r.json())
  .then(profile => console.log(profile.workout_count));
```

## How it works

```
Your GitHub Actions (every 10 min, free)
  ├── Headless Chrome → logs into Hevy (your credentials)
  ├── Gets fresh API tokens
  └── Pushes tokens to your Vercel project
         │
         ▼
Your Vercel deployment
  └── Serves your Hevy data via HTTP API
```

## Files

| File | Purpose |
|------|---------|
| `hevy.py` | Python client library (25+ endpoints) |
| `hevy_login.py` | Headless login script |
| `vercel/` | Next.js API proxy |
| `.github/workflows/hevy-refresh.yml` | Auto-refresh cron |
| `SETUP.md` | Full deployment guide |
| `hevy-api-reference.md` | Full API surface docs |
