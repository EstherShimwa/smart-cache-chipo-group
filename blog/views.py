# blog/views.py
#
# =============================================================================
#  SMART CACHE LAYER — GUIDED ACTIVITY
#  Advanced Python Programming | ALU BSE
# =============================================================================
#
#  This file contains three API views. Your job is to add caching to each one.
#  Read each TODO carefully — they build on each other.
#
#  Run the timing script first (docs/ACTIVITY.md → Level 1) to see
#  how slow the uncached responses are before you begin.
# =============================================================================

import time
import logging

from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import Post
from .serializers import PostSerializer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache keys — one source of truth for GET (read) and POST (invalidate)
# ---------------------------------------------------------------------------

POSTS_LIST_KEY = "posts:list"
POSTS_LIST_VERSION_KEY = "posts:list:version"
POSTS_LIST_TTL = 300          # 5 minutes — list changes often
POST_DETAIL_TTL = 600         # 10 minutes — a single post changes rarely


def _posts_list_cache_key(query_string: str = "") -> str:
    """Shared list key, plus query params so filters/pages don't collide.

    Stretch goal: ``?status=published`` and ``?page=2`` each get their own entry.
    The version prefix lets Level 4 bust every variant at once — LocMemCache
    has no ``delete_pattern``.
    """
    version = cache.get(POSTS_LIST_VERSION_KEY) or 0
    suffix = query_string or "all"
    return f"{POSTS_LIST_KEY}:v{version}:{suffix}"


def _invalidate_posts_list_cache() -> None:
    """Level 4 — drop the canonical key and bump the version.

    Bumping the version makes every query-aware key (``posts:list:vN:...``)
    unreachable. Old entries expire on their own TTL.
    """
    cache.delete(POSTS_LIST_KEY)
    version = cache.get(POSTS_LIST_VERSION_KEY) or 0
    cache.set(POSTS_LIST_VERSION_KEY, version + 1, timeout=None)


def _post_detail_cache_key(post_id: int) -> str:
    return f"posts:detail:{post_id}"


def _drafts_cache_key(user_id: int) -> str:
    return f"drafts:user:{user_id}"


# ---------------------------------------------------------------------------
# LEVEL 2 — Shared Cache (Public Data)
# ---------------------------------------------------------------------------

class PostListView(APIView):
    """
    GET  /api/posts/       — Returns all published posts.
    POST /api/posts/       — Creates a new post (authenticated users only).
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        # Shared key: every caller sees the same published list.
        # Stretch: query params are part of the key so pages/filters don't collide.
        params = request.query_params.urlencode()
        cache_key = _posts_list_cache_key(params)

        data = cache.get(cache_key)
        if data is not None:                     # HIT
            return Response(data)

        # MISS: query the DB, then cache-aside
        posts = Post.objects.filter(status=Post.STATUS_PUBLISHED).select_related("author")
        data = PostSerializer(posts, many=True).data
        cache.set(cache_key, data, timeout=POSTS_LIST_TTL)
        cache.set(POSTS_LIST_KEY, data, timeout=POSTS_LIST_TTL)
        return Response(data)

    def post(self, request):
        # ---------------------------------------------------------------
        # LEVEL 4 — Invalidate after mutation so GET is never stale.
        #
        # cache.delete() drops the old entry; the next GET rebuilds from DB.
        # That is safer than writing the new list into the cache here:
        # we would have to rebuild every query-aware variant correctly.
        # Write-through is better for a single object we already serialized.
        # ---------------------------------------------------------------

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save(author=request.user)

            # Always bust the published list — a new published post must appear,
            # and a status change away from draft would also change the list.
            _invalidate_posts_list_cache()

            if post.status == Post.STATUS_PUBLISHED:
                # Write-through: we already have the serialized object.
                cache.set(
                    _post_detail_cache_key(post.id),
                    serializer.data,
                    timeout=POST_DETAIL_TTL,
                )
            else:
                # A new draft would otherwise stay invisible until TTL (2 min).
                cache.delete(_drafts_cache_key(request.user.id))

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# LEVEL 2 (continued) — Single Post Cache
# ---------------------------------------------------------------------------

class PostDetailView(APIView):
    """
    GET /api/posts/<post_id>/ — Returns a single published post.
    """

    permission_classes = [AllowAny]

    def get(self, request, post_id: int):
        # Unique per post. Longer TTL is fine: one post mutates less than the list.
        cache_key = _post_detail_cache_key(post_id)

        data = cache.get(cache_key)
        if data is not None:                     # HIT
            return Response(data)

        try:
            post = Post.objects.select_related("author").get(
                id=post_id, status=Post.STATUS_PUBLISHED
            )
        except Post.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        data = PostSerializer(post).data
        cache.set(cache_key, data, timeout=POST_DETAIL_TTL)
        return Response(data)


# ---------------------------------------------------------------------------
# LEVEL 3 — User-Isolated Cache (Personal Data)
# ---------------------------------------------------------------------------

class MyDraftsView(APIView):
    """
    GET /api/posts/my-drafts/ — Returns draft posts for the logged-in user only.

    !! SECURITY CRITICAL !!
    This endpoint returns private data. Every student must ensure
    that User A can never see User B's drafts under any circumstances.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # SECURITY: the key includes the user's ID, so every user gets their own
        # cache entry. With a shared key like "my-drafts", the first user's drafts
        # would be served to every other user.
        cache_key = _drafts_cache_key(request.user.id)

        data = cache.get(cache_key)
        if data is not None:                     # HIT
            return Response(data)

        # MISS: query the DB
        drafts = Post.objects.filter(
            author=request.user,
            status=Post.STATUS_DRAFT
        ).select_related("author")
        data = PostSerializer(drafts, many=True).data

        cache.set(cache_key, data, timeout=120)  # 2 minutes
        return Response(data)


# ---------------------------------------------------------------------------
# BONUS — Deliberately Broken View (Level 3 Bug-Spotting)
# ---------------------------------------------------------------------------

class BrokenDraftsView(APIView):
    """
    GET /api/posts/broken-drafts/

    This view has a critical security bug.
    Your task: read the code, find the bug, and explain it in the activity sheet.
    DO NOT fix the code here — write your answer in docs/ACTIVITY.md.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # !! BUG: find it, name it, explain the real-world impact !!
        data = cache.get("my-drafts")
        if data is None:
            drafts = Post.objects.filter(
                author=request.user,
                status=Post.STATUS_DRAFT
            ).select_related("author")
            serializer = PostSerializer(drafts, many=True)
            data = serializer.data
            cache.set("my-drafts", data, timeout=120)
        return Response(data)
