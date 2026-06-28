"""
Demo script showing Hevy API client usage.
Run with: python demo.py
"""
from hevy import from_token, HevyClient

# Use a token obtained from the browser session
TOKEN = "your_access_token_here"
USER_ID = "your_user_id_here"

client = from_token(TOKEN, USER_ID)

# ── My Account ──────────────────────────────────────────────
print("=" * 50)
print("MY ACCOUNT")
acct = client.get_my_account()
print(f"  Username:    {acct.username}")
print(f"  Email:       {acct.email}")
print(f"  Created:     {acct.created_at[:10]}")

# ── User Profile ────────────────────────────────────────────
print("=" * 50)
print("ALLSTAR PROFILE")
profile = client.get_user_profile("allstar")
print(f"  Name:        {profile.full_name}")
print(f"  Workouts:    {profile.workout_count}")
print(f"  Followers:   {profile.follower_count:,}")
print(f"  Following:   {profile.following_count:,}")
print(f"  Routines:    {len(profile.routines)}")
if profile.weekly_workout_durations:
    latest = profile.weekly_workout_durations[-1]
    secs = latest["total_seconds"]
    print(f"  Last week:   {secs // 3600}h {secs % 3600 // 60}m")

# ── Workout Detail ──────────────────────────────────────────
print("=" * 50)
print("LATEST WORKOUT (allstar)")
w = client.get_workout("y8KlgFRgNLH")
print(f"  Title:       {w.name}")
print(f"  Volume:      {w.estimated_volume_kg:,.0f} kg")
print(f"  Duration:    {(w.end_time - w.start_time) // 60}m")
print(f"  Likes:       {w.like_count}     Comments: {w.comment_count}")
print(f"  Exercises:")
for ex in w.exercises:
    sets = ex["sets"]
    total_sets = len(sets)
    total_reps = sum(s["reps"] for s in sets)
    total_wt = sum(s["weight_kg"] * s["reps"] for s in sets)
    print(f"    {ex['title']}: {total_sets} sets, {total_reps} reps, {total_wt:,.0f} kg vol")

# ── Workout Feed ────────────────────────────────────────────
print("=" * 50)
print("FEED")
feed = client.get_feed_workouts()
print(f"  Items:       {len(feed.get('workouts', []))}")

# ── Recommended Users ───────────────────────────────────────
print("=" * 50)
print("RECOMMENDED USERS")
for u in client.get_recommended_users()[:5]:
    print(f"  @{u.username:20s}  {u.full_name[:30]}" if u.full_name else f"  @{u.username}")

# ── Subscription ────────────────────────────────────────────
print("=" * 50)
print("SUBSCRIPTION")
sub = client.get_my_subscription()
print(f"  Pro:         {sub['is_pro']}")

print("=" * 50)
print("DONE")
