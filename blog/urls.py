# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("posts/", views.PostListView.as_view(), name="post-list"),
    path("posts/my-drafts/", views.MyDraftsView.as_view(), name="my-drafts"),
    path("posts/broken-drafts/", views.BrokenDraftsView.as_view(), name="broken-drafts"),
    path("posts/<int:post_id>/", views.PostDetailView.as_view(), name="post-detail"),
]
