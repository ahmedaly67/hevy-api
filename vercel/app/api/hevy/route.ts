/**
 * Next.js API route — Hevy proxy
 *
 * Endpoints:
 *   GET  /api/hevy/workouts       — feed workouts
 *   GET  /api/hevy/workouts/:id   — workout detail
 *   GET  /api/hevy/profile/:user  — user profile
 *   GET  /api/hevy/me             — my account
 *   GET  /api/hevy/routines       — my routines
 *   GET  /api/hevy/users          — recommended users
 *
 * Query params: ?username=&shortId=&limit=&offset=
 */

import { NextRequest, NextResponse } from "next/server";
import { HevyClient } from "@/lib/hevy";
import { readTokens } from "@/lib/tokens";

// Single shared client instance (cached per request handler)
function getClient() {
  return new HevyClient(() => readTokens());
}

// POST handler — forwards requests to Hevy API
export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get("_path") || "";

  try {
    const client = getClient();
    const body = await request.json().catch(() => ({}));

    // Special probe mode
    if (path === "probe_all") {
      const results: Record<string, any> = {};
      const endpoints = body.endpoints || [];

      for (const ep of endpoints) {
        const key = `${ep.method || "POST"} ${ep.path}`;
        try {
          const res = await client.rawRequest(ep.method || "POST", ep.path, ep.body || {});
          results[key] = res;
        } catch (e: any) {
          results[key] = { error: e.message };
        }
      }
      return NextResponse.json({ results });
    }

    // General POST forwarding
    const data = await client.rawRequest("POST", path, body);
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get("_path") || "";

  try {
    const client = getClient();
    let data: unknown;

    switch (path) {
      case "workouts":
        data = await client.getFeedWorkouts();
        break;
      case "workout":
        data = await client.getWorkout(
          searchParams.get("shortId") || ""
        );
        break;
      case "profile": {
        const username = searchParams.get("username") || "demoacc";
        data = await client.getUserProfile(username);
        break;
      }
      case "me":
        data = await client.getMyAccount();
        break;
      case "routines":
        data = await client.syncRoutines();
        break;
      case "users":
        data = await client.getRecommendedUsers();
        break;
      case "workout-count":
        data = await client.getWorkoutCount();
        break;
      case "health":
        return NextResponse.json({
          status: "ok",
          provider: "hevy",
          has_access_token: Boolean(process.env.HEVY_ACCESS_TOKEN),
          token_length: (process.env.HEVY_ACCESS_TOKEN || "").length,
        });
      case "debug":
        // Raw test: call Hevy API directly
        try {
          const tok = process.env.HEVY_ACCESS_TOKEN || "";
          const rawRes = await fetch("https://api.hevyapp.com/user/account", {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${tok}`,
              "x-api-key": "shelobs_hevy_web",
              "hevy-platform": "web",
              "x-client-time": String(Date.now() / 1000),
              "Accept": "application/json",
            },
          });
          const rawBody = await rawRes.text();
          return NextResponse.json({
            status: rawRes.status,
            headers: Object.fromEntries(rawRes.headers.entries()),
            body: rawBody.substring(0, 500),
          });
        } catch (e: any) {
          return NextResponse.json({ error: e.message }, { status: 500 });
        }
      default:
        return NextResponse.json(
          { error: "Unknown path. Use: workouts, workout, profile, me, routines, users" },
          { status: 400 }
        );
    }

    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
      },
    });
  } catch (err: any) {
    console.error("[hevy] API error:", err.message, err.stack);
    return NextResponse.json(
      {
        error: err.message || "Internal error",
        detail: process.env.NODE_ENV === "development" ? err.stack : undefined,
      },
      { status: 500 }
    );
  }
}
