/**
 * Hevy Private API Client — TypeScript (Vercel-compatible)
 *
 * Pure HTTP client, no browser needed. Tokens must be supplied
 * externally (via Vercel KV, env vars, or a token refresh service).
 */
const BASE_URL = "https://api.hevyapp.com";
const API_KEY = "shelobs_hevy_web";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user_id: string;
  expires_at: string;
}

export interface UserAccount {
  id: string;
  username: string;
  email: string;
  country_code: string;
  city: string;
  is_pro?: boolean;
  private_profile: boolean;
  created_at: string;
  last_workout_at: string;
  is_coached: boolean;
  is_a_coach: boolean;
}

export interface UserProfile {
  username: string;
  full_name: string;
  profile_pic: string | null;
  description: string;
  workout_count: number;
  follower_count: number;
  following_count: number;
  private_profile: boolean;
  routines: Array<{ id: string; title: string; short_id: string }>;
  weekly_workout_durations: Array<{
    week_start_date: string;
    total_seconds: number;
  }>;
}

export interface WorkoutDetail {
  id: string;
  short_id: string;
  name: string;
  username: string;
  description: string;
  start_time: number;
  end_time: number;
  estimated_volume_kg: number;
  like_count: number;
  comment_count: number;
  exercises: Array<{
    title: string;
    muscle_group: string;
    sets: Array<{
      weight_kg: number;
      reps: number;
      rpe: number | null;
      indicator: string;
    }>;
  }>;
  comments: Array<{
    username: string;
    comment: string;
    created_at: string;
    like_count: number;
  }>;
}

export interface RecommendedUser {
  id: string;
  username: string;
  full_name: string;
  profile_pic: string | null;
  following_status: string | null;
}

export type TokenProvider = () => Promise<AuthTokens | null>;

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class HevyClient {
  private tokens: AuthTokens | null = null;
  private getTokens: TokenProvider;

  constructor(getTokens: TokenProvider) {
    this.getTokens = getTokens;
  }

  private async ensureTokens(): Promise<AuthTokens> {
    if (this.tokens && !this._isExpired(this.tokens)) {
      return this.tokens;
    }
    const fresh = await this.getTokens();
    if (!fresh) throw new Error("No valid Hevy tokens available");
    this.tokens = fresh;
    return fresh;
  }

  private _isExpired(t: AuthTokens): boolean {
    try {
      const expiry = new Date(t.expires_at).getTime();
      return Date.now() >= expiry;
    } catch {
      return true;
    }
  }

  private async request<T>(method: string, path: string, json?: unknown): Promise<T> {
    const tokens = await this.ensureTokens();
    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        "x-api-key": API_KEY,
        "hevy-platform": "web",
        "x-client-time": String(Date.now() / 1000),
        Authorization: `Bearer ${tokens.access_token}`,
        Accept: "application/json",
        ...(json ? { "Content-Type": "application/json" } : {}),
      },
      ...(json ? { body: JSON.stringify(json) } : {}),
      cache: "no-store",
    });

    if (!res.ok) {
      if (res.status === 401) {
        this.tokens = null; // force re-fetch on next call
        throw new Error("Hevy token expired");
      }
      throw new Error(`Hevy API error: ${res.status} ${await res.text().catch(() => "")}`);
    }

    return res.json() as Promise<T>;
  }

  private _get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<T>("GET", `${path}${qs}`);
  }

  private _post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  // Raw request — exposes any method/path for debugging
  async rawRequest(method: string, path: string, body?: unknown): Promise<any> {
    try {
      return await this.request<any>(method, path, body);
    } catch (e: any) {
      return { _error: e.message, _status: e.message?.match(/Hevy API error: (\d+)/)?.[1] };
    }
  }

  // ── Account ──
  getMyAccount() { return this._get<any>("/user/account"); }
  getMySubscription() { return this._get<{ is_pro: boolean }>("/user_subscription"); }
  getMyPreferences() { return this._get<any>("/user_preferences"); }

  // ── Profiles ──
  getUserProfile(username: string) {
    return this._get<any>(`/user_profile/${username}`);
  }

  // ── Workouts ──
  getWorkout(shortId: string) { return this._get<any>(`/workout/${shortId}`); }
  getUserWorkouts(username: string, limit = 10, offset = 0) {
    return this._get<any>("/user_workouts_paged", {
      username,
      limit: String(limit),
      offset: String(offset),
    });
  }
  getFeedWorkouts() { return this._get<any>("/feed_workouts_paged"); }
  getWorkoutCount() { return this._get<{ workout_count: number }>("/workout_count"); }

  // ── Routines ──
  syncRoutines() { return this._post<any>("/routines_sync_batch"); }
  getRoutineFolders() { return this._get<any[]>("/routine_folders"); }
  createRoutine(title: string, exercises: Array<{
    exercise_template_id: string;
    rest_seconds?: number;
    sets: Array<{ index: number; indicator?: string }>;
    notes?: string;
  }>) {
    return this._post<any>("/routine?sendSyncEventToMobileApp=true", {
      routine: {
        title,
        exercises: exercises.map(e => ({
          exercise_template_id: e.exercise_template_id,
          rest_seconds: e.rest_seconds ?? 60,
          sets: e.sets,
          notes: e.notes ?? "",
        })),
        folder_id: null,
        index: 0,
        program_id: null,
        notes: null,
        coach_force_rpe_enabled: false,
      },
    });
  }

  // ── Social ──
  getRecommendedUsers() { return this._get<any[]>("/recommended_users"); }
  getFollowingStatuses() { return this._get<any[]>("/following_statuses"); }
  getFollowCounts() { return this._get<any>("/follow_counts"); }

  // ── Stats ──
  getUserWorkoutImages(username: string, count = 5) {
    return this._get<any[]>(`/user_workout_images/${username}/${count}`);
  }
  getCalendarWorkouts(year: number, month: number) {
    return this._get<any>(`/user_calendar_workouts/${year}/${month}`);
  }
}
