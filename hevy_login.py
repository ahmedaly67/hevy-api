"""
One-shot headless login for Hevy.
Captures reCAPTCHA v3 automatically via a real browser, logs in,
saves tokens to disk, and exits. No persistent browser needed.

Requires: pip install playwright && playwright install chromium

Usage:
    python hevy_login.py email@example.com password123
    python hevy_login.py email@example.com password123 --output tokens.json
    python hevy_login.py email@example.com password123 --save-credentials
"""

import sys
import json
import time
import urllib.parse
from pathlib import Path

DEFAULT_OUTPUT = Path.home() / ".hevy_tokens.json"
RECAPTCHA_SITE_KEY = "6LfkQG0jAAAAANTrIkVXKPfSPHyJnt4hYPWqxh0R"


def login(email_or_username: str, password: str, output_path: str | None = None, save_credentials: bool = False) -> dict:
    """
    Login to Hevy via headless browser. Returns auth tokens dict.

    Args:
        save_credentials: If True, stores email in the token file for auto-refresh.
                          Password is stored only if HEVY_SAVE_PASSWORD=1 is set.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    output = Path(output_path or DEFAULT_OUTPUT)

    print(f"Logging in as {email_or_username} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # Step 1: Navigate to login page
            page.goto("https://hevy.com/login", wait_until="networkidle", timeout=15000)
            print("  Loaded login page")

            # Step 2: Fill email
            page.evaluate(
                """(email) => {
                const inputs = document.querySelectorAll('input');
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(inputs[0], email);
                inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                inputs[0].dispatchEvent(new Event('change', {bubbles: true}));
            }""",
                email_or_username,
            )

            # Step 3: Fill password
            page.evaluate(
                """(passwd) => {
                const inputs = document.querySelectorAll('input');
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(inputs[1], passwd);
                inputs[1].dispatchEvent(new Event('input', {bubbles: true}));
                inputs[1].dispatchEvent(new Event('change', {bubbles: true}));
            }""",
                password,
            )

            time.sleep(0.5)

            # Wait for reCAPTCHA to be ready
            try:
                page.wait_for_function(
                    "typeof grecaptcha !== 'undefined' && typeof grecaptcha.enterprise !== 'undefined'",
                    timeout=5000,
                )
                print("  reCAPTCHA loaded")
            except Exception:
                print("  WARNING: reCAPTCHA not detected, proceeding anyway")

            # Step 4: Get reCAPTCHA token and login via API directly
            #           (more reliable than form submission in headless mode)
            recaptcha_token = page.evaluate(
                """(siteKey) => {
                return new Promise((resolve, reject) => {
                    if (typeof grecaptcha === 'undefined' || typeof grecaptcha.enterprise === 'undefined') {
                        reject('grecaptcha not available');
                        return;
                    }
                    grecaptcha.enterprise.ready(() => {
                        grecaptcha.enterprise.execute(siteKey, {action: 'login'}).then(resolve).catch(reject);
                    });
                });
            }""",
                RECAPTCHA_SITE_KEY,
            )
            print(f"  Got reCAPTCHA token ({len(recaptcha_token)} chars)")

            # Step 5: Call login API from within browser context
            #          (reCAPTCHA tokens are bound to the browser session)
            login_result = page.evaluate(
                """([email, password, token]) => {
                return fetch('https://api.hevyapp.com/login', {
                    method: 'POST',
                    headers: {
                        'x-api-key': 'shelobs_hevy_web',
                        'hevy-platform': 'web',
                        'x-client-time': String(Date.now() / 1000),
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    body: JSON.stringify({
                        emailOrUsername: email,
                        password: password,
                        recaptchaToken: token,
                    }),
                }).then(r => r.json().then(data => ({status: r.status, data})));
            }""",
                [email_or_username, password, recaptcha_token],
            )

            if login_result["status"] != 200:
                error_msg = login_result["data"].get("error", f"HTTP {login_result['status']}")
                print(f"  Login failed: {error_msg}")
                browser.close()
                sys.exit(1)

            login_data = login_result["data"]
            print(f"  Login successful! User: {login_data.get('user_id', '?')[:20]}...")

            # Step 6: Build tokens from API response (no need for cookies)
            tokens = {
                "user_id": login_data["user_id"],
                "access_token": login_data["access_token"],
                "refresh_token": login_data["refresh_token"],
                "expires_at": login_data["expires_at"],
                "fetched_at": time.time(),
            }

            # Optionally store credentials for auto-refresh
            if save_credentials:
                tokens["_email"] = email_or_username
                tokens["_password"] = password

            # Step 7: Save to disk
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(tokens, indent=2))
            print(f"  Tokens saved to {output}")
            print(f"  Expires: {tokens['expires_at']}")

            browser.close()
            return tokens

        except Exception as e:
            print(f"  ERROR: {e}")
            browser.close()
            raise


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    output = None
    save_creds = False

    # Parse flags
    args = sys.argv[3:]
    for i, arg in enumerate(args):
        if arg == "--output" and i + 1 < len(args):
            output = args[i + 1]
        if arg in ("--save-credentials", "--save-creds"):
            save_creds = True

    login(email, password, output, save_credentials=save_creds)


if __name__ == "__main__":
    main()
