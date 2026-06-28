export default function Home() {
  return (
    <div style={{ fontFamily: "system-ui", maxWidth: 800, margin: "0 auto", padding: 40 }}>
      <h1>Hevy API Proxy — Vercel</h1>
      <p>This is a Vercel-ready proxy for the Hevy private API.</p>

      <h2>Endpoints</h2>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "2px solid #ddd" }}>
            <th style={{ padding: 8 }}>Method</th>
            <th style={{ padding: 8 }}>Path</th>
            <th style={{ padding: 8 }}>Params</th>
            <th style={{ padding: 8 }}>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=me</b></code></td>
            <td style={{ padding: 8 }}>—</td>
            <td style={{ padding: 8 }}>My account</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=workouts</b></code></td>
            <td style={{ padding: 8 }}>—</td>
            <td style={{ padding: 8 }}>Feed workouts</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=workout</b>&shortId=xxx</code></td>
            <td style={{ padding: 8 }}>shortId</td>
            <td style={{ padding: 8 }}>Workout detail</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=profile</b>&username=allstar</code></td>
            <td style={{ padding: 8 }}>username</td>
            <td style={{ padding: 8 }}>User profile</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=routines</b></code></td>
            <td style={{ padding: 8 }}>—</td>
            <td style={{ padding: 8 }}>My routines</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #eee" }}>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=users</b></code></td>
            <td style={{ padding: 8 }}>—</td>
            <td style={{ padding: 8 }}>Recommended users</td>
          </tr>
          <tr>
            <td style={{ padding: 8 }}>GET</td>
            <td style={{ padding: 8 }}><code>/api/hevy?<b>_path=health</b></code></td>
            <td style={{ padding: 8 }}>—</td>
            <td style={{ padding: 8 }}>Health check</td>
          </tr>
        </tbody>
      </table>

      <h2>Setup</h2>
      <pre style={{ background: "#f5f5f5", padding: 16, borderRadius: 8 }}>
{`1. Set environment variables on Vercel:
   HEVY_ACCESS_TOKEN=xxx
   HEVY_USER_ID=xxx
   HEVY_REFRESH_TOKEN=xxx
   HEVY_TOKEN_EXPIRES=2026-... (ISO date)

2. Or use Vercel KV + GitHub Actions auto-refresh:
   Set secrets: HEVY_EMAIL, HEVY_PASSWORD,
   VERCEL_KV_REST_API_URL, VERCEL_KV_REST_API_TOKEN

3. Get initial tokens by running:
   python hevy_login.py email@example.com password --save-credentials
   → copy tokens from ~/.hevy_tokens.json`}
      </pre>
    </div>
  );
}
