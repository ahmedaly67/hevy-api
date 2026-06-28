"""Probe Hevy API for POST/creation endpoints using Playwright."""
import os, json

SITE_KEY = '6LfkQG0jAAAAANTrIkVXKPfSPHyJnt4hYPWqxh0R'

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Login
    page.goto('https://hevy.com/login', wait_until='networkidle', timeout=15000)
    page.wait_for_timeout(3000)

    token = page.evaluate('''(sk) => {
        return new Promise((res, rej) => {
            grecaptcha.enterprise.ready(() => {
                grecaptcha.enterprise.execute(sk, {action: 'login'}).then(res).catch(rej);
            });
        });
    }''', SITE_KEY)

    result = page.evaluate('''([email, passwd, t]) => {
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
    }''', [os.environ.get('HEVY_EMAIL', 'thediamondhasdied@gmail.com'),
           os.environ.get('HEVY_PASSWORD', ''), token])

    if result['status'] != 200:
        print(f"Login failed: {result['data']}")
        browser.close()
        exit(1)

    print(f"Login OK. User: {result['data']['user_id']}")
    access_token = result['data']['access_token']

    # Core API probe function
    def probe(method, path, platform='web', body='{}', api_key='shelobs_hevy_web'):
        r = page.evaluate('''([m, p, t, plat, b, key]) => {
            return fetch('https://api.hevyapp.com' + p, {
                method: m,
                headers: {
                    'x-api-key': key,
                    'hevy-platform': plat,
                    'Authorization': 'Bearer ' + t,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: b,
            }).then(r => r.text().then(data => ({status: r.status, data})));
        }''', [method, path, access_token, platform, body, api_key])
        return r.get('status'), r.get('data', '')[:200]

    print('\n=== PHASE 1: WORKOUT CREATION ENDPOINTS (web) ===')
    endpoints = [
        ('POST', '/workout'),
        ('POST', '/workouts'),
        ('POST', '/workout/create'),
        ('POST', '/workout/start'),
        ('POST', '/workouts/create'),
        ('POST', '/create_workout'),
        ('POST', '/workout_event'),
        ('POST', '/create_workout_event'),
        ('POST', '/workout_session'),
        ('POST', '/log_workout'),
        ('POST', '/routine_workout'),
    ]
    for method, path in endpoints:
        status, body = probe(method, path)
        if status not in (404, 405):
            print(f"  {method} {path} -> {status}: {body}")

    print('\n=== PHASE 2: EXERCISE/SET LOGGING (web) ===')
    endpoints = [
        ('POST', '/workout_exercise'),
        ('POST', '/workout/exercise'),
        ('POST', '/workout/set'),
        ('POST', '/workout_set'),
        ('POST', '/log_set'),
        ('POST', '/log_exercise'),
        ('POST', '/exercise/log'),
        ('POST', '/set'),
    ]
    for method, path in endpoints:
        status, body = probe(method, path)
        if status not in (404, 405):
            print(f"  {method} {path} -> {status}: {body}")

    print('\n=== PHASE 3: SOCIAL ACTIONS (web) ===')
    endpoints = [
        ('POST', '/follow'),
        ('POST', '/unfollow'),
        ('POST', '/like'),
        ('POST', '/comment'),
        ('POST', '/workout/like'),
        ('POST', '/workout/comment'),
    ]
    for method, path in endpoints:
        status, body = probe(method, path)
        if status not in (404, 405):
            print(f"  {method} {path} -> {status}: {body}")

    print('\n=== PHASE 4: MOBILE PLATFORM HEADERS ===')
    mobile_endpoints = [
        ('POST', '/workout'),
        ('POST', '/workouts'),
        ('POST', '/workout/start'),
        ('POST', '/workout/set'),
        ('POST', '/workout_event'),
        ('POST', '/v1/workout'),
        ('POST', '/v2/workout'),
        ('POST', '/log_workout'),
    ]
    for plat in ['ios', 'android']:
        for method, path in mobile_endpoints:
            status, body = probe(method, path, platform=plat)
            if status not in (404, 405):
                print(f"  {plat}: {method} {path} -> {status}: {body}")

    print('\n=== PHASE 5: DIFFERENT API KEYS ===')
    keys_to_try = [
        ('shelobs_hevy', 'shorter variant'),
        ('hevy_mobile', 'mobile variant'),
        ('hevy_ios', 'ios variant'),
        ('hevy_android', 'android variant'),
    ]
    for key, desc in keys_to_try:
        status, body = probe('POST', '/workout', api_key=key)
        print(f"  {desc} ({key}): {status}")

    print('\n=== PHASE 6: PROFILE/PUT ENDPOINTS ===')
    endpoints = [
        ('PUT', '/me'),
        ('PATCH', '/me'),
        ('POST', '/profile/update'),
        ('POST', '/user/update'),
        ('PUT', '/user'),
    ]
    for method, path in endpoints:
        status, body = probe(method, path)
        if status not in (404, 405):
            print(f"  {method} {path} -> {status}: {body}")

    browser.close()
    print('\nDone.')
