/**
 * Token storage for Hevy auth on Vercel.
 * Reads tokens from environment variables. GitHub Actions pushes new tokens
 * via the Vercel API / Vercel env vars.
 */
import type { AuthTokens } from "./hevy";

/**
 * Read tokens from environment variables.
 * Set these on Vercel: HEVY_ACCESS_TOKEN, HEVY_USER_ID, etc.
 */
export async function readTokens(): Promise<AuthTokens | null> {
  // Try JSON blob first
  const env = process.env.HEVY_TOKENS;
  if (env) {
    try {
      return JSON.parse(env);
    } catch { /* ignore */ }
  }

  // Individual env vars
  const token = process.env.HEVY_ACCESS_TOKEN;
  const userId = process.env.HEVY_USER_ID;
  if (token && userId) {
    return {
      access_token: token,
      refresh_token: process.env.HEVY_REFRESH_TOKEN || "",
      user_id: userId,
      expires_at: process.env.HEVY_TOKEN_EXPIRES || "2099-01-01T00:00:00.000Z",
    };
  }

  return null;
}

/**
 * Check if hevy is configured (tokens exist).
 */
export async function isConfigured(): Promise<boolean> {
  return (await readTokens()) !== null;
}
