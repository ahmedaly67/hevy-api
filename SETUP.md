# Hevy Private API — Full Setup Guide

Reverse-engineered, fully automated client for the Hevy workout tracker private API.  
Deployable on Vercel with GitHub Actions auto-refresh. **$0 cost.**

---

## What you get

| Component | What it does |
|-----------|-------------|
| `hevy.py` | Python client library (25+ endpoints, full dataclass models) |
| `hevy_login.py` | One-shot headless login script (solves reCAPTCHA via Playwright) |
| `vercel/` | Next.js serverless API proxy deployable to Vercel |
| `.github/workflows/hevy-refresh.yml` | Auto-refresh cron — logs in every 10 min, pushes tokens to Vercel |
| `hevy-api-reference.md` | Full API surface documentation |

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  GitHub Actions (every 10 min, free)         │
│                                              │
│  1. Spins up Ubuntu with Chrome              │
│  2. Opens hevy.com/login                     │
│  3. Generates reCAPTCHA v3 Enterprise token   │
│  4. POST /login → gets fresh tokens          │
│  5. Pushes tokens to Vercel env vars via API │
└────────────────────┬─────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│  Vercel (hosts your API proxy)               │
│                                              │
│  /api/hevy?_path=profile&username=allstar    │
│  /api/hevy?_path=workout&shortId=xxx         │
│  /api/hevy?_path=users                       │
│  /api/hevy?_path=routines                    │
│  /api/hevy?_path=me                          │
│  /api/hevy?_path=workouts                    │
│  /api/hevy?_path=health                      │
└──────────────────────────────────────────────┘
```

---

## Step 1: Get the code

```bash
git clone https://github.com/ahmedaly67/hevy-api.git
cd hevy-api
```

Or copy these files from the repo to your own:
- `hevy.py` — Python API client
- `hevy_login.py` — Login script
- `vercel/` — Vercel Next.js app
- `.github/workflows/hevy-refresh.yml` — Auto-refresh

---

## Step 2: Install dependencies

```bash
# Python client
pip install playwright requests

# Headless Chrome (needed once)
playwright install chromium

# Vercel deployment
cd vercel
npm install
npm install -g vercel
```

---

## Step 3: Test locally with Python

```bash
# Login once (this saves tokens to ~/.hevy_tokens.json)
python hevy_login.py your@email.com yourpassword --save-credentials

# Use the client
python -c "
from hevy import from_file
client = from_file()  # auto-refreshes when expired
print('Account:', client.get_my_account().username)
print('Workout count:', client.get_workout_count())
profile = client.get_user_profile('allstar')
print(f'Followers: {profile.follower_count:,}')
"
```

If `--save-credentials` fails due to rate limiting, wait 2 minutes and try again.

---

## Step 4: Deploy the API proxy to Vercel

### 4a: Set up your Vercel account
1. Go to [vercel.com](https://vercel.com) and sign up (free tier is enough)
2. Install the Vercel CLI: `npm install -g vercel`
3. Login: `vercel login`

### 4b: Deploy
```bash
cd vercel

# Deploy
vercel --prod

# The CLI will ask for project name, scope, etc.
# Answer "yes" to link to existing project if prompted.
```

Note the **project ID** from the output (looks like `prj_xxxxxxxxxxxxx`) and your **team/scope name** (run `vercel teams list` to find it).

### 4c: Set initial env vars
```bash
# Grab a fresh token first
python ../hevy_login.py your@email.com yourpassword --save-credentials

# Read the tokens
python -c "import json; t=json.load(open('../test_tokens.json')); print(t['access_token'])"
python -c "import json; t=json.load(open('../test_tokens.json')); print(t['refresh_token'])"
python -c "import json; t=json.load(open('../test_tokens.json')); print(t['expires_at'])"

# Set them on Vercel (replace with your values)
echo "ACCESS_TOKEN_VALUE" | vercel env add HEVY_ACCESS_TOKEN production --yes
echo "REFRESH_TOKEN_VALUE" | vercel env add HEVY_REFRESH_TOKEN production --yes
echo "EXPIRES_AT_VALUE" | vercel env add HEVY_TOKEN_EXPIRES production --yes
vercel env add HEVY_USER_ID production --yes
# → when prompted, paste: f6f07f54-da89-42fc-92ca-5fcde1372b02

# Redeploy to pick up env vars
vercel --prod --yes
```

Your API is now live at `https://your-project.vercel.app`.

### 4d: Test
```bash
curl "https://your-project.vercel.app/api/hevy?_path=health"
# → {"status":"ok","provider":"hevy",...}

curl "https://your-project.vercel.app/api/hevy?_path=me"
# → {"id":"...","username":"...","email":"...",...}

curl "https://your-project.vercel.app/api/hevy?_path=profile&username=allstar"
# → {"username":"allstar","workout_count":1835,...}
```

---

## Step 5: Set up auto-refresh (GitHub Actions)

Tokens expire every ~20 minutes. The GitHub Action re-logs in every 10 minutes.

### 5a: Create a GitHub repo
```bash
cd /path/to/hevy-api  # the root of this project
git init
git add -A
git commit -m "Initial commit"
```

Create a new repo on GitHub (private recommended since it holds your login), then:
```bash
git remote add origin https://github.com/YOUR_USER/hevy-api.git
git push -u origin main
```

### 5b: Set GitHub repository secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

Add these secrets:

| Secret Name | Value | Where to find it |
|-------------|-------|-----------------|
| `HEVY_EMAIL` | `your@email.com` | Your Hevy login email |
| `HEVY_PASSWORD` | `yourpassword` | Your Hevy login password |
| `VERCEL_TOKEN` | `vcp_xxxxxxxxxxxxx` | [vercel.com/account/tokens](https://vercel.com/account/tokens) → Create Token |
| `VERCEL_PROJECT_ID` | `prj_xxxxxxxxxxxxx` | From Step 4b (or `vercel project ls`) |
| `VERCEL_ORG_ID` | `your-team-name` | Run `vercel teams list` to find it |

### 5c: Verify it works
Go to your repo → **Actions** → **Refresh Hevy Tokens** → **Run workflow**.

It should complete in ~50 seconds with a ✅.

The workflow runs every 10 minutes automatically from now on.

---

## Step 6: Use the API from your dashboard

### From a browser (JavaScript)
```javascript
// Get a user's profile
const res = await fetch(
  'https://your-project.vercel.app/api/hevy?_path=profile&username=allstar'
);
const profile = await res.json();
console.log(`${profile.full_name} — ${profile.workout_count} workouts`);

// Get recommended users
const users = await fetch(
  'https://your-project.vercel.app/api/hevy?_path=users'
).then(r => r.json());

// Get a specific workout
const workout = await fetch(
  'https://your-project.vercel.app/api/hevy?_path=workout&shortId=y8KlgFRgNLH'
).then(r => r.json());
```

### From Python (server-side)
```python
import requests

def get_hevy(path, **params):
    url = f"https://your-project.vercel.app/api/hevy?_path={path}"
    for k, v in params.items():
        url += f"&{k}={v}"
    return requests.get(url).json()

profile = get_hevy("profile", username="allstar")
print(profile["workout_count"])  # 1835
```

### From a health/fitness dashboard
```html
<div id="hevy-stats">
  <span id="workout-count">...</span>
  <span id="volume">...</span>
</div>
<script>
  fetch('/api/hevy?_path=profile&username=YOUR_USERNAME')
    .then(r => r.json())
    .then(data => {
      document.getElementById('workout-count').textContent = data.workout_count;
    });
</script>
```

---

## API Endpoint Reference

All endpoints use `GET` with query parameters:

| `_path` | Params | Returns |
|---------|--------|---------|
| `health` | — | `{"status":"ok"}` |
| `me` | — | Full account info (username, email, etc.) |
| `users` | — | 7 recommended/follow-suggested users |
| `profile` | `username=allstar` | Full profile: routines, durations, followers |
| `workout` | `shortId=y8KlgFRgNLH` | Exercise sets, reps, weights, comments, HR data |
| `workouts` | — | Feed workouts from people you follow |
| `routines` | — | Your routines with exercises and sets |

---

## Troubleshooting

### "Login failed" in GitHub Action
- Your Hevy credentials are wrong. Update `HEVY_EMAIL` / `HEVY_PASSWORD` secrets.
- Rate limited. Wait 5 minutes and try again.

### 500 errors from Vercel
- Token expired before the auto-refresh ran. Manually trigger the GitHub Action.
- Or run `python hevy_login.py ...` locally and update Vercel env vars manually.

### "Project not found" in GitHub Action
- `VERCEL_PROJECT_ID` or `VERCEL_ORG_ID` secrets are wrong.
- Run `vercel project ls` and `vercel teams list` to get correct values.

### reCAPTCHA not loading (Playwright error)
- GitHub's runner might have network issues. The workflow retries on the next cron.
- If persistent, try running `python hevy_login.py` locally to verify.

---

## Security notes

- **Keep your repo private.** It contains your Hevy email/password as GitHub secrets.
- The Vercel token has broad access. Use one scoped to just that project if possible.
- This is a **private/unoffical API**. Hevy could change or block it at any time.
- Don't hammer the API. The default 10-minute refresh schedule is gentle.

---

## Files in this repo

```
├── hevy.py                          # Python client library
├── hevy_login.py                    # Headless login script
├── hevy-api-reference.md            # Full API surface docs
├── demo.py                          # Python usage demo
├── .gitignore
├── .github/workflows/
│   └── hevy-refresh.yml             # Auto-refresh GitHub Action
└── vercel/                          # Vercel deployment
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx                 # Landing page (API docs)
    │   └── api/hevy/route.ts        # API proxy route
    └── lib/
        ├── hevy.ts                  # TypeScript Hevy client
        └── tokens.ts                # Token storage
```
