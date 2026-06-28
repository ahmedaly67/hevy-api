"""Explore Hevy web app with Playwright, capture ALL API requests."""
import os, json

SITE_KEY = '6LfkQG0jAAAAANTrIkVXKPfSPHyJnt4hYPWqxh0R'
API_REQUESTS = []

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    def capture_req(req):
        if 'api.hevyapp' in req.url and req.method != 'OPTIONS':
            API_REQUESTS.append({
                'method': req.method,
                'url': req.url.replace('https://api.hevyapp.com', ''),
                'post_data': req.post_data,
                'headers': dict(req.headers),
            })

    page.on('request', capture_req)

    # Login
    page.goto('https://hevy.com/login', wait_until='networkidle', timeout=15000)
    page.wait_for_timeout(3000)

    token = page.evaluate("""(sk) => {
        return new Promise((res, rej) => {
            grecaptcha.enterprise.ready(() => {
                grecaptcha.enterprise.execute(sk, {action: 'login'}).then(res).catch(rej);
            });
        });
    }""", SITE_KEY)

    result = page.evaluate("""([email, passwd, t]) => {
        return fetch('https://api.hevyapp.com/login', {
            method: 'POST',
            headers: {
                'x-api-key': 'shelobs_hevy_web',
                'hevy-platform': 'web',
                'x-client-time': String(Date.now() / 1000),
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({emailOrUsername: email, password: passwd, recaptchaToken: t}),
        }).then(r => r.json().then(data => ({status: r.status, data})));
    }""", [os.environ.get('HEVY_EMAIL', 'thediamondhasdied@gmail.com'),
           os.environ.get('HEVY_PASSWORD', ''), token])

    if result['status'] != 200:
        print(f'Login failed: {result["data"]}')
        browser.close()
        exit(1)

    access_token = result['data']['access_token']
    print(f'Login OK: {result["data"]["user_id"]}')

    # Navigate to main app
    page.goto('https://hevy.com', wait_until='networkidle', timeout=15000)
    page.wait_for_timeout(4000)

    # Check what pages/routes are available
    routes = page.evaluate("""() => {
        const links = Array.from(document.querySelectorAll('a[href]'));
        return links.map(l => ({
            href: l.getAttribute('href'),
            text: l.textContent.trim().substring(0, 40)
        })).filter(x => x.text && x.href);
    }""")

    print('\n=== Available routes ===')
    for r in routes[:30]:
        if r['href'] and r['href'].startswith('/'):
            print(f"  {r['href']:40s} {r['text']}")

    # Click to routines page
    print('\n=== Navigating to routines ===')
    try:
        page.goto('https://hevy.com/routines', wait_until='networkidle', timeout=10000)
        page.wait_for_timeout(3000)
    except:
        print('  No routines page found')

    # Try profile page
    try:
        page.goto(f'https://hevy.com/demoacc', wait_until='networkidle', timeout=10000)
        page.wait_for_timeout(3000)
    except:
        print('  No profile page found')

    browser.close()

    # Print all captured API requests
    print(f'\n=== CAPTURED API REQUESTS ({len(API_REQUESTS)}) ===')
    seen = set()
    for r in API_REQUESTS:
        key = f"{r['method']} {r['url']}"
        if key not in seen:
            seen.add(key)
            body = r['post_data'] or ''
            if len(body) > 300:
                body = body[:300] + '...'
            print(f"  {key}")
            if body:
                print(f"    POST data: {body}")
    
    # Also try direct API calls with the token
    print('\n=== DIRECT API PROBING ===')
    api_endpoints = [
        ('POST', '/workout', {'name': 'Test workout', 'description': 'test'}),
        ('POST', '/workout', {'title': 'Test workout', 'exercise_ids': []}),
        ('POST', '/v2/workout', {'name': 'Test'}),
        ('POST', '/v2/workout', {'title': 'Test'}),
        ('POST', '/workout_event', {}),
        ('POST', '/workout_events', {}),
        ('POST', '/start_workout', {}),
        ('POST', '/workout/start', {}),
        ('POST', '/end_workout', {}),
        ('POST', '/complete_workout', {}),
        ('POST', '/finish_workout', {}),
        # With mobile-like bodies
        ('POST', '/workout', {
            'workout': {
                'name': 'Test',
                'description': '',
                'start_time': '2026-06-28T15:00:00Z',
                'end_time': '2026-06-28T16:00:00Z',
            }
        }),
        ('POST', '/v2/workout', {
            'workout': {
                'name': 'Test',
                'description': '',
                'start': 1719590400,
                'end': 1719594000,
            }
        }),
    ]

    for method, path, body in api_endpoints:
        result = page.evaluate("""([m, p, b, t]) => {
            return fetch('https://api.hevyapp.com' + p, {
                method: m,
                headers: {
                    'x-api-key': 'shelobs_hevy_web',
                    'hevy-platform': 'web',
                    'Authorization': 'Bearer ' + t,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(b),
            }).then(r => r.text().then(data => ({status: r.status, data: data.substring(0, 300)})));
        }""", [method, path, body, access_token])

        status = result.get('status', 'error')
        body_text = result.get('data', '')
        if status not in (404, 405, 401):
            print(f"  {method} {path} -> {status}: {body_text}")
