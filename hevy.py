"""
Hevy Private API Client Library
================================
Reversed from the Hevy web app (https://hevy.com).
Handles authentication, token management, and all known endpoints.
"""

from __future__ import annotations

import sys
import time
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict, fields
from typing import Optional, Literal, overload, get_type_hints
from datetime import datetime, timezone, timedelta
import requests


_MISSING = object()

def _construct(cls: type, data: dict) -> object:
    """Create a dataclass from a dict, filling missing keys from field defaults."""
    kwargs = {}
    for f in fields(cls):
        if f.name in data:
            kwargs[f.name] = data[f.name]
        elif f.default is not _MISSING:
            kwargs[f.name] = f.default
        elif f.default_factory is not _MISSING:
            kwargs[f.name] = f.default_factory()
    return cls(**kwargs)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.hevyapp.com"
API_KEY = "shelobs_hevy_web"
PLATFORM = "web"
RECAPTCHA_SITE_KEY = "6LfkQG0jAAAAANTrIkVXKPfSPHyJnt4hYPWqxh0R"

MuscleGroup = Literal[
    "chest", "biceps", "triceps", "shoulders", "upper_back",
    "lower_back", "quadriceps", "hamstrings", "glutes", "calves",
    "abdominals", "forearms", "abductors", "adductors", "cardio", "full_body",
]

EquipmentCategory = Literal[
    "machine", "barbell", "dumbbell", "cable", "bodyweight",
    "kettlebell", "band", "suspension", "smith_machine",
]

SetIndicator = Literal["normal", "warmup", "failure", "drop_set"]
PRType = Literal["best_volume", "best_1rm"]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class AuthTokens:
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: str  # ISO-8601

    @property
    def is_expired(self) -> bool:
        return datetime.fromisoformat(self.expires_at) < datetime.now(timezone.utc)


@dataclass
class UserAccount:
    id: str
    username: str
    email: str
    is_strava_connected: bool
    is_chatgpt_oauth_authorized: bool
    country_code: str
    city: str
    likes_push_enabled: bool
    follows_push_enabled: bool
    comments_push_enabled: bool
    comment_mention_push_enabled: bool
    comment_discussion_push_enabled: bool
    private_profile: bool
    created_at: str
    last_workout_at: str
    accepted_terms_and_conditions: bool
    is_coached: bool
    is_a_coach: bool
    email_consent: bool
    email_verified: bool
    is_hevy_trainer_user: bool


@dataclass
class UserPreferences:
    username: str
    language: str
    first_weekday: str
    superset_scrolling: bool
    plate_calculator_enabled: bool
    rpe_enabled: bool
    inline_set_timer_enabled: bool
    default_workout_visibility_public: bool
    volume_includes_warmup_sets: bool


@dataclass
class RoutineSummary:
    id: str
    title: str
    short_id: str
    folder_id: Optional[int]


@dataclass
class WeeklyDuration:
    week_start_date: str
    week_end_date: str
    total_seconds: int


@dataclass
class UserProfile:
    username: str = ""
    verified: bool = False
    subscribed: bool = False
    profile_pic: Optional[str] = None
    full_name: str = ""
    description: str = ""
    website_link: Optional[str] = None
    workout_count: int = 0
    is_blocked: bool = False
    following_status: Optional[str] = None
    is_followed_by_requester: bool = False
    private_profile: bool = False
    follower_count: int = 0
    following_count: int = 0
    routines: list[dict] = field(default_factory=list)
    weekly_workout_durations: list[dict] = field(default_factory=list)
    mutual_followers: list = field(default_factory=list)


@dataclass
class PersonalRecord:
    type: str
    value: float


@dataclass
class WorkoutSet:
    id: str
    index: int
    weight_kg: float
    reps: int
    rpe: Optional[float]
    indicator: str
    completed_at: str
    prs: list[dict]
    personal_records: list
    custom_metric: Optional[dict]
    distance_meters: Optional[float]
    duration_seconds: Optional[int]


@dataclass
class ExerciseEntry:
    id: str
    exercise_template_id: str
    title: str
    muscle_group: str
    equipment_category: str
    exercise_type: str
    media_type: Optional[str]
    url: Optional[str]
    thumbnail_url: Optional[str]
    priority: int
    rest_seconds: int
    notes: str
    superset_id: Optional[str]
    volume_doubling_enabled: bool
    custom_exercise_image_url: Optional[str]
    sets: list[WorkoutSet] = field(default_factory=list)
    de_title: Optional[str] = None
    es_title: Optional[str] = None
    fr_title: Optional[str] = None
    it_title: Optional[str] = None
    ja_title: Optional[str] = None
    ko_title: Optional[str] = None
    pt_title: Optional[str] = None
    ru_title: Optional[str] = None
    tr_title: Optional[str] = None
    zh_cn_title: Optional[str] = None
    zh_tw_title: Optional[str] = None
    other_muscles: list[str] = field(default_factory=list)


@dataclass
class Biometrics:
    total_calories: int
    average_heart_rate: int
    heart_rate_samples: list[dict] = field(default_factory=list)


@dataclass
class Comment:
    id: int
    comment: str
    username: str
    verified: bool
    full_name: str
    profile_pic: Optional[str]
    created_at: str
    like_count: int
    is_liked_by_user: bool
    parent_comment_id: Optional[int] = None


@dataclass
class WorkoutDetail:
    id: str
    short_id: str
    name: str
    index: int
    username: str
    user_id: str
    description: str
    start_time: int
    end_time: int
    created_at: str
    updated_at: str
    is_private: bool
    is_home_gym: bool
    apple_watch: bool
    wearos_watch: bool
    nth_workout: int
    like_count: int
    comment_count: int
    profile_image: Optional[str]
    estimated_volume_kg: float
    include_warmup_sets: bool
    is_biometrics_public: bool
    is_liked_by_user: bool
    exercises: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    media: list[dict] = field(default_factory=list)
    image_urls: list[str] = field(default_factory=list)
    like_images: list[str] = field(default_factory=list)
    preview_workout_likes: list[dict] = field(default_factory=list)
    biometrics: Optional[dict] = None


@dataclass
class RecommendedUser:
    id: str
    username: str
    verified: bool
    full_name: str
    profile_pic: Optional[str]
    following_status: Optional[str]
    private_profile: bool
    following: bool
    label: Optional[str]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class HevyClient:
    """Client for the Hevy private API."""

    def __init__(
        self,
        recaptcha_token_provider: Optional[callable] = None,
        base_url: str = BASE_URL,
        api_key: str = API_KEY,
    ):
        """
        Args:
            recaptcha_token_provider: A callable that returns a fresh reCAPTCHA
                Enterprise token. If not provided, login will fail unless you
                supply the token directly to .login().
            base_url: API base URL.
            api_key: Client API key (default is the web client key).
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._recaptcha_provider = recaptcha_token_provider
        self._tokens: Optional[AuthTokens] = None
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _headers(self) -> dict:
        """Base headers for every request."""
        h = {
            "x-api-key": self.api_key,
            "hevy-platform": PLATFORM,
            "x-client-time": str(time.time()),
            "Accept": "application/json",
        }
        if self._tokens and self._tokens.access_token:
            h["Authorization"] = f"Bearer {self._tokens.access_token}"
        return h

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        r = self._session.request(
            method, url, headers=self._headers, params=params, json=json_body
        )
        if r.status_code == 401:
            raise HevyAuthError(r.json().get("error", "Unauthorized"))
        r.raise_for_status()
        return r

    def _get(self, path: str, params: dict | None = None) -> dict:
        return self._request("GET", path, params=params).json()

    def _post(self, path: str, body: dict | None = None) -> dict:
        return self._request("POST", path, json_body=body or {}).json()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(
        self,
        email_or_username: str,
        password: str,
        recaptcha_token: Optional[str] = None,
    ) -> AuthTokens:
        """
        Authenticate and store tokens.

        Use a recaptcha_token_provider passed to __init__ or supply the
        token directly here (one must be provided).
        """
        if recaptcha_token is None and self._recaptcha_provider:
            recaptcha_token = self._recaptcha_provider()

        if not recaptcha_token:
            raise HevyError(
                "reCAPTCHA token required. Provide recaptcha_token_provider "
                "to HevyClient() or pass recaptcha_token to login()."
            )

        body = {
            "emailOrUsername": email_or_username,
            "password": password,
            "recaptchaToken": recaptcha_token,
        }
        # Login doesn't use Bearer auth (no token yet), only x-api-key
        r = self._session.request(
            "POST",
            f"{self.base_url}/login",
            headers={
                "x-api-key": self.api_key,
                "hevy-platform": PLATFORM,
                "x-client-time": str(time.time()),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=body,
        )
        if r.status_code != 200:
            raise HevyAuthError(r.json().get("error", f"Login failed ({r.status_code})"))

        data = r.json()
        self._tokens = AuthTokens(**data)
        return self._tokens

    def refresh(self) -> AuthTokens:
        """Attempt token refresh.  Not observed on web — may be mobile-only."""
        raise NotImplementedError(
            "Token refresh endpoint not yet discovered. Login again."
        )

    # ------------------------------------------------------------------
    # User / Account
    # ------------------------------------------------------------------

    def get_my_account(self) -> UserAccount:
        """Get the currently authenticated user's account info."""
        return _construct(UserAccount, self._get("/user/account"))

    def get_my_subscription(self) -> dict:
        """Get subscription status."""
        return self._get("/user_subscription")

    def get_my_preferences(self) -> UserPreferences:
        """Get user preferences/settings."""
        return _construct(UserPreferences, self._get("/user_preferences"))

    def get_user_key_values(self) -> dict:
        """Get user key-value metadata."""
        return self._get("/user_key_values")

    def get_user_profile(self, username: str) -> UserProfile:
        """Get public profile for any user."""
        return _construct(UserProfile, self._get(f"/user_profile/{username}"))

    # ------------------------------------------------------------------
    # Workouts
    # ------------------------------------------------------------------

    def get_workout(self, short_id: str) -> WorkoutDetail:
        """Get full workout detail by short ID."""
        return _construct(WorkoutDetail, self._get(f"/workout/{short_id}"))

    def get_user_workouts(
        self, username: str, limit: int = 20, offset: int = 0
    ) -> dict:
        """Get a user's workout list (paginated)."""
        return self._get(
            "/user_workouts_paged",
            params={"username": username, "limit": limit, "offset": offset},
        )

    def get_feed_workouts(self) -> dict:
        """Get social feed workouts."""
        return self._get("/feed_workouts_paged")

    def get_workout_count(self) -> int:
        """Get current user's total workout count."""
        data = self._get("/workout_count")
        return data.get("workout_count", 0)

    def get_workout_images(self, username: str, count: int = 5) -> list:
        """Get recent workout thumbnail images for a user."""
        return self._get(f"/user_workout_images/{username}/{count}")

    def get_workout_duration_metrics(
        self, start_ts: int, end_ts: int
    ) -> list:
        """Get duration metrics over a time range (Unix timestamps)."""
        return self._get(f"/user_workout_metrics/duration/{start_ts}/{end_ts}")

    def get_calendar_workouts(self, year: int, month: int) -> dict:
        """Get workout calendar data for a month."""
        return self._get(f"/user_calendar_workouts/{year}/{month}")

    # ------------------------------------------------------------------
    # Routines
    # ------------------------------------------------------------------

    def sync_routines(self) -> dict:
        """Sync routines (bidirectional)."""
        return self._post("/routines_sync_batch")

    def create_routine(
        self,
        title: str,
        exercises: list[dict],
        folder_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Create a new routine.

        exercises: list of dicts like:
            {
                "exercise_template_id": "79D0BB3A",
                "rest_seconds": 60,
                "sets": [{"index": 0, "indicator": "normal"}],
                "notes": ""
            }
        Returns {"routineId": "uuid"}.
        """
        body = {
            "routine": {
                "title": title,
                "exercises": exercises,
                "folder_id": folder_id,
                "index": 0,
                "program_id": None,
                "notes": notes,
                "coach_force_rpe_enabled": False,
            }
        }
        return self._request(
            "POST", "/routine?sendSyncEventToMobileApp=true", json_body=body
        ).json()

    def get_routine_folders(self) -> list:
        """Get routine folders."""
        return self._get("/routine_folders")

    def get_custom_exercise_templates(self) -> list:
        """Get user's custom exercise templates."""
        return self._get("/custom_exercise_templates")

    def get_exercise_template_units(self) -> list:
        """Get exercise template units."""
        return self._get("/exercise_template_units")

    # ------------------------------------------------------------------
    # Social
    # ------------------------------------------------------------------

    def get_following_statuses(self) -> list:
        """Get follow status for relevant users."""
        return self._get("/following_statuses")

    def get_follow_counts(self) -> dict:
        """Get follower/following counts for current user."""
        return self._get("/follow_counts")

    def get_recommended_users(self) -> list[RecommendedUser]:
        """Get featured/recommended users."""
        return [_construct(RecommendedUser, u) for u in self._get("/recommended_users")]

    # ------------------------------------------------------------------
    # Coach / Trainer
    # ------------------------------------------------------------------

    def get_client_invites(self) -> list:
        """Get coach client invitations."""
        return self._get("/client_invites")

    def get_clients_coach(self) -> list:
        """Get clients list (coach view). Returns 404 if not a coach."""
        return self._get("/clients_coach")

    def get_trainer_program(self) -> dict:
        """Get Hevy Trainer guided program data."""
        return self._get("/hevy_trainer/program")

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def get_paddle_prices(self) -> dict:
        """Get Paddle subscription pricing."""
        return self._get("/paddle_prices")

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def get_full_profile(self, username: str) -> dict:
        """Get a user's complete profile including workouts."""
        profile = self.get_user_profile(username)
        workouts = self.get_user_workouts(username)
        images = self.get_workout_images(username, count=10)
        return {
            "profile": asdict(profile),
            "recent_workouts": workouts,
            "images": images,
        }

    def iter_user_workouts(self, username: str, limit: int = 20):
        """Generator that paginates through all of a user's workouts."""
        offset = 0
        while True:
            data = self.get_user_workouts(username, limit=limit, offset=offset)
            workouts = data.get("workouts", [])
            if not workouts:
                break
            for w in workouts:
                yield w
            offset += len(workouts)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class HevyError(Exception):
    """Base exception for Hevy API errors."""


class HevyAuthError(HevyError):
    """Authentication failed."""


# ---------------------------------------------------------------------------
# Quick-start factories
# ---------------------------------------------------------------------------

def from_token(access_token: str, user_id: str) -> HevyClient:
    """
    Create a client from a manually obtained access token (e.g. from
    the Network tab). No reCAPTCHA needed for this path.
    """
    client = HevyClient()
    client._tokens = AuthTokens(
        user_id=user_id,
        access_token=access_token,
        refresh_token="",
        expires_at="2099-01-01T00:00:00.000Z",
    )
    return client


def from_file(path: str = "~/.hevy_tokens.json") -> HevyClient:
    """Load tokens from disk (written by hevy_login.py). Auto-refreshes on expiry."""
    import subprocess
    from pathlib import Path

    token_file = Path(path).expanduser()

    if not token_file.exists():
        raise FileNotFoundError(
            f"Token file not found: {token_file}\n"
            f"Run: python hevy_login.py your@email.com yourpassword"
        )

    data = json.loads(token_file.read_text())

    access_token = data.get("access_token", "")
    user_id = data.get("user_id", "")
    expires_at = data.get("expires_at", "")
    email = data.get("_email", "")
    password = data.get("_password", "")

    # Check if manual token is still valid
    if expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at)
            if expiry > datetime.now(timezone.utc):
                client = HevyClient()
                client._tokens = AuthTokens(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=data.get("refresh_token", ""),
                    expires_at=expires_at,
                )
                client._token_file = token_file
                return client
        except (ValueError, TypeError):
            pass

    # Token expired or no expiry — refresh via headless login
    if not email or not password:
        raise HevyError(
            "Token expired and no email/password stored for auto-refresh.\n"
            "Re-run: python hevy_login.py your@email.com yourpassword"
        )

    print("[hevy] Token expired, auto-refreshing via headless login...")

    # Run hevy_login.py in the same directory as this file
    login_script = Path(__file__).parent / "hevy_login.py"
    if not login_script.exists():
        login_script = Path("hevy_login.py")

    result = subprocess.run(
        [sys.executable, str(login_script), email, password, "--output", str(token_file)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise HevyError(
            f"Auto-refresh failed: {result.stderr or result.stdout}"
        )

    # Reload tokens
    data = json.loads(token_file.read_text())
    client = HevyClient()
    client._tokens = AuthTokens(
        user_id=data["user_id"],
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        expires_at=data.get("expires_at", ""),
    )
    client._token_file = token_file
    print("[hevy] Token refreshed successfully")
    return client


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Hevy API Client loaded.")
    print()
    print("Server-side / dashboard usage (recommended):")
    print("  # Step 1: Login once (saves tokens to disk, auto-refreshes)")
    print("  python hevy_login.py your@email.com yourpassword")
    print()
    print("  # Step 2: Use the client (auto-refreshes when needed)")
    print("  from hevy import from_file")
    print("  client = from_file()")
    print("  account = client.get_my_account()")
    print()
    print("One-shot usage (token from browser Network tab):")
    print("  from hevy import from_token")
    print("  client = from_token('token_here', 'user_id_here')")
