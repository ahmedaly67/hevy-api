# Hevy API Client

Reverse-engineered private API client + Vercel proxy for the [Hevy](https://hevy.com) workout tracker. Auto-refreshes every 10 minutes via GitHub Actions. **$0 cost.**

## Quick Start (to use the hosted API)

Your friend's API is live at:

```
https://vercel-nine-xi-30.vercel.app/api/hevy
```

### Endpoints

| `?path=` | Extra params | Returns |
|-----------|-------------|---------|
| `me` | — | Your Hevy account |
| `profile` | `&username=allstar` | Any user's profile, routines, workout history |
| `workout` | `&shortId=y8KlgFRgNLH` | Full workout detail (sets, reps, weights, HR) |
| `users` | — | Recommended users |
| `workouts` | — | Feed |
| `routines` | — | Your routines |
| `health` | — | Status check |

### Usage (from any website/app)

```javascript
// Get a user's profile
const res = await fetch(
  'https://vercel-nine-xi-30.vercel.app/api/hevy?_path=profile&username=allstar'
);
const profile = await res.json();
// → { username: "allstar", workout_count: 1835, follower_count: 12578, ... }
```

```python
import requests

r = requests.get(
    'https://vercel-nine-xi-30.vercel.app/api/hevy',
    params={'_path': 'profile', 'username': 'allstar'}
)
print(r.json()['workout_count'])  # 1835
```

---

## Setup your own instance

Follow [SETUP.md](SETUP.md) for a complete step-by-step guide. You'll need:
- A Hevy account
- A GitHub account
- A Vercel account (free)

Takes ~15 minutes.

---

## How it works

```
GitHub Actions (every 10 min)
  ├── Headless Chrome → logs into Hevy
  ├── Gets fresh API tokens
  ├── Pushes tokens to Vercel env vars via REST API
  └── Triggers Vercel redeploy
         │
         ▼
Vercel (hosts the API proxy)
  └── Reads fresh tokens → serves Hevy data
```

---

## Files

| File | Purpose |
|------|---------|
| `hevy.py` | Python client library (25+ endpoints) |
| `hevy_login.py` | Headless login script (solves reCAPTCHA via Playwright) |
| `vercel/` | Next.js API proxy |
| `.github/workflows/hevy-refresh.yml` | Auto-refresh every 10 min |
| `SETUP.md` | Full deployment guide |
| `hevy-api-reference.md` | Complete API surface docs |
