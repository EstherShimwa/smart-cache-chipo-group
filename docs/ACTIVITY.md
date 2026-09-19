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
| All Posts | ___ms | ___ms |
| Single Post | ___ms | ___ms |

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

_Your answer:_

---

> Walk through this exact scenario — what happens step by step?
> 1. Alice logs in and calls `/api/posts/broken-drafts/`
> 2. Bob logs in and calls `/api/posts/broken-drafts/`

_Your answer:_

---

> What is the real-world impact of this bug if it shipped to production?

_Your answer:_

---

> What is the one-line fix?

_Your answer:_

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

---

## Final Check — Run the Timer One More Time

```bash
python timing.py
```

**Record your final results:**

| Endpoint | Before (Level 1) | After (Level 4) | Improvement |
|----------|-----------------|-----------------|-------------|
| All Posts | ___ms | ___ms | ___% faster |
| Single Post | ___ms | ___ms | ___% faster |

---

## Reflection Questions

Answer these before the debrief:

1. Why did you use a **shared** key for `/api/posts/` but a **user-specific** key for `/my-drafts/`?

2. What would happen if you set `timeout=None` on the post list cache?

3. In what situation would caching `/my-drafts/` actually cause a bug even with the correct user-specific key?
   *(Hint: think about what happens when a user saves a new draft)*

---

## Key Concepts Checklist

By the end of this activity you should be able to:

- [ ] Explain what cache-aside (lazy loading) means in your own words
- [ ] Design a cache key that is shared, user-specific, or query-aware as needed
- [ ] Explain why authentication must happen **before** the cache lookup
- [ ] Implement cache invalidation when underlying data changes
- [ ] Identify a cache key bug and explain its security impact

---

*Built for ALU BSE — Advanced Python Programming*
