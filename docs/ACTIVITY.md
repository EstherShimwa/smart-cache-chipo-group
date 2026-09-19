# Smart Cache Layer — Guided Activity

**Course:** Advanced Python Programming | ALU BSE  
**Topic:** Caching  
**Duration:** ~30 minutes  
**File to work in:** `blog/views.py`

---

## Overview

You have been given a working Django REST API for a blog platform with 500 posts
and 3 users. The API works — but it hits the database on **every single request**.

Your job is to add a smart cache layer, level by level, until the API is fast,
correct, and secure.

---

## Setup

```bash
# 1. Clone the repo and enter the directory
git clone <repo-url>
cd smart-cache-activity

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations and seed the database
python manage.py migrate
python manage.py seed

# 5. Start the server
python manage.py runserver
```

You should see output confirming 500 posts and 3 users created:
```
✅ Created user: alice / password123
✅ Created user: bob / password123
✅ Created user: carol / password123
✅ Created 500 posts
```

---

## The Endpoints

| Method | URL | What it does | Auth required? |
|--------|-----|--------------|----------------|
| GET | `/api/posts/` | All published posts | No |
| GET | `/api/posts/<id>/` | Single published post | No |
| POST | `/api/posts/` | Create a new post | Yes |
| GET | `/api/posts/my-drafts/` | Your own drafts only | Yes |
| GET | `/api/posts/broken-drafts/` | Buggy draft view | Yes |

---

## Level 1 — Feel the Pain (5 min)

Before writing any cache code, run the timing script to record your baseline:

```bash
# Make sure the server is running in another terminal first
python timing.py
```

**Record your results here:**

| Endpoint | First Request | Average |
|----------|--------------|---------|
| All Posts | 36.4ms | 13.5ms |
| Single Post | 2.1ms | 1.2ms |

You'll run this again after each level to see how much you've improved.

---

## Level 2 — Cache the Public Data (15 min)

Open `blog/views.py` and find the `PostListView` and `PostDetailView` classes.

Follow the TODO comments to implement **cache-aside** for both endpoints.

**The pattern you are implementing:**
```
Request comes in
    ↓
Check cache → HIT?  → Return cached data immediately (fast ⚡)
    ↓ MISS
Query database
    ↓
Store result in cache
    ↓
Return data to user
```

**Tools available:**
```python
from django.core.cache import cache

cache.get("your-key")                      # returns None if not found
cache.set("your-key", data, timeout=300)   # stores data for 300 seconds
```

**When you're done**, run `python timing.py` again and compare.

> **Discussion:** What cache key did you choose for the list endpoint?
> Compare with a classmate — did you choose the same key? Why or why not?

We used a **shared** key, `posts:list`, because published posts are public — every caller should see the same list. A username in the key would waste memory with duplicate copies of identical data. The stretch goal extends this to `posts:list:v{version}:{query}` so `?page=2` cannot overwrite the unfiltered list, and Level 4 can bust every variant by bumping the version.

---

## Level 3 — Protect Personal Data (15 min)

Now find the `MyDraftsView` class and implement caching for the `/my-drafts/` endpoint.

**This one is different.** The drafts belong to a specific user — you must ensure
that **User A can never see User B's drafts**, even through the cache.

### Step 1 — Implement the cache

Follow the TODO in `MyDraftsView.get()`. Think carefully about your cache key.

### Step 2 — Find the bug

Look at `BrokenDraftsView` at the bottom of `views.py`.

**Do NOT fix the code.** Instead, answer these questions below:

---

**Bug Report**

> What is the bug in `BrokenDraftsView`?

The bug in `BrokenDraftsView` is that it uses a hardcoded cache key, "my-drafts" instead of a per-user-key. 
This means that all users share one single cache entry. Once any user's drafts are cached under that key, the following user who hits the endpoint
gets a cache hit and gets the first user's drafts until the entry expires.

---

> Walk through this exact scenario — what happens step by step?
> 1. Alice logs in and calls `/api/posts/broken-drafts/`
> 2. Bob logs in and calls `/api/posts/broken-drafts/`

1. Alice will log in and call `/api/posts/broken-drafts/`. `cache.get("my-drafts")` returns None, so the database is
queried for Alice's drafts. The results are serialized and stored in the cache under the key `"my-drafts"` with a 120-seconds timeout.\n
\n

2. Bob will log in and call `/api/posts/broken-drafts/` within the 120-seconds window. `cache.get("my-drafts")` now returns
a value, so the database is not queried for Bob at all. His own drafts he doesn't receive, he receives Alice's stored drafts.

---

> What is the real-world impact of this bug if it shipped to production?

Drafts are any work that the author has not yet decided to publish. This bug would affect any authenticated user who calls the endpoint 
after one user has already called it. They would receive the previous user's draft content from the storage cache. This bug is dangerous because it fails silently with no errors thrown and a 200 OK response. It could run for a long time without being caught and continuously leaking data.

---

> What is the one-line fix?

`cache_key = f"drafts:user:{request.user.id}"` is the one line fix I would implement to replace the hardcoded cache key 
with a per-user cache key. I would also update the `cache.get()` and `cache.set()` to match the pattern used in `MyDraftsView`
---

## Level 4 — Invalidation (10 min)

You've now cached the post list. But there's a problem.

**Scenario:**
1. User requests `GET /api/posts/` — gets cached response (100 posts)
2. User creates a new post via `POST /api/posts/`
3. User requests `GET /api/posts/` again — **still sees 100 posts, not 101**

The cache doesn't know the data changed.

### Your task

Find the `post()` method in `PostListView` and add the one line of code
that fixes this problem after a new post is saved.

```python
cache.delete("your-key-here")   # removes the stale entry
```

**Test it:**
1. Call `GET /api/posts/` and note the count
2. Call `POST /api/posts/` to create a new post
3. Call `GET /api/posts/` again — the new post should appear

> **Discussion:** What's the difference between `cache.delete()` and
> updating the cache with the new data directly? When would you choose each?

`cache.delete()` **invalidates**: it drops the stale entry. The next GET is a miss and rebuilds from the database. That is the safe default for a **list**, because the cached value is a full queryset (and, with the stretch goal, several query-aware variants). Rebuilding the exact cached shape on every POST is easy to get wrong.

Updating the cache directly is **write-through**: you already have the new object, so you `cache.set` it. We do that for a newly created **published** post (`posts:detail:{id}`), because the serializer data is already in hand.

Choose delete for collections / many keys. Choose write-through for a single object you just saved.

**Tested:** `GET /api/posts/` cached the published list, `POST` created a new published post, the next `GET` returned count+1 and included the new title. Creating a draft also deletes `drafts:user:{id}` so Person 3's cache cannot hide the new draft.

---

## Stretch Goal — Query-Aware Cache Key

If you finish early, look at this scenario:

```
GET /api/posts/?status=published    # all published posts
GET /api/posts/?status=published&page=2   # page 2 only
```

If you used a single key like `"posts:all"` for both, they'd overwrite each other.

**Challenge:** Modify your `PostListView.get()` so that the cache key
accounts for any query parameters in the request.

```python
# Hint — something like this:
params = request.query_params.urlencode()   # turns params into a string
cache_key = f"posts:list:{params}"
```

Implemented in `PostListView.get()`. The live key is `posts:list:v{version}:{params or "all"}`. Level 4 bumps `posts:list:version` on POST so every query-aware variant is busted at once (LocMemCache has no `delete_pattern`).

---

## Final Check — Run the Timer One More Time

```bash
python timing.py
```

**Record your final results:**

| Endpoint | Before (Level 1) | After (Level 4) | Improvement |
|----------|-----------------|-----------------|-------------|
| All Posts | 36.4ms (cache miss / DB) | 1.8ms (cache hit) | ~95% faster |
| Single Post | 2.1ms (cache miss / DB) | 0.8ms (cache hit) | ~62% faster |

---

## Reflection Questions

Answer these before the debrief:

1. Why did you use a **shared** key for `/api/posts/` but a **user-specific** key for `/my-drafts/`?

   Published posts are the same for every caller, so one shared key (`posts:list`) is correct and cheaper. Drafts are private. A shared key would leak User A's drafts to User B (exactly the `BrokenDraftsView` bug). The drafts key must include `request.user.id`.

2. What would happen if you set `timeout=None` on the post list cache?

   The entry would never expire on its own. After a restart the LocMemCache is empty anyway, but while the process is up the list would stay stale forever **unless** we invalidate on write. That is why Level 4's `cache.delete` / version bump is required — TTL is a safety net, not a substitute for invalidation. `timeout=None` plus missing invalidation = users never see new posts.

3. In what situation would caching `/my-drafts/` actually cause a bug even with the correct user-specific key?
   *(Hint: think about what happens when a user saves a new draft)*

   If a user creates a new draft via `POST /api/posts/` while `drafts:user:{id}` is still warm, the next `GET /my-drafts/` would return the **old** list until the 120s TTL expires. Correct isolation does not fix staleness. Level 4 deletes that user's drafts key when the new post is a draft.

---

## Key Concepts Checklist

By the end of this activity you should be able to:

- [x] Explain what cache-aside (lazy loading) means in your own words
- [x] Design a cache key that is shared, user-specific, or query-aware as needed
- [x] Explain why authentication must happen **before** the cache lookup
- [x] Implement cache invalidation when underlying data changes
- [x] Identify a cache key bug and explain its security impact

---

*Built for ALU BSE — Advanced Python Programming*
