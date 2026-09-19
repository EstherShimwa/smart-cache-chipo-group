# blog/serializers.py

from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    """Serializes a Post instance for API output."""

    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "content", "author_username", "status", "created_at"]
        read_only_fields = ["id", "created_at", "author_username"]
