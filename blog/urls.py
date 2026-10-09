from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),
    path("blog/", views.blog_index, name="blog"),
    path("contact/", views.contact, name="contact"),
    path("subscribe/", views.subscribe_page, name="subscribe_page"),
    path("subscribe/join/", views.subscribe, name="subscribe"),
    path("privacy/", views.privacy, name="privacy"),
    path("accessibility/", views.accessibility, name="accessibility"),
    path("search/", views.search, name="search"),
    path("category/<slug:slug>/", views.category_list, name="category"),
    path("tag/<slug:slug>/", views.tag_list, name="tag"),
    path("author/<str:username>/", views.author_posts, name="author"),
    path("write/", views.post_create, name="create"),
    path("write/preview/", views.markdown_preview, name="preview"),
    path("my-posts/", views.my_posts, name="my_posts"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("post/<slug:slug>/", views.post_detail, name="detail"),
    path("post/<slug:slug>/edit/", views.post_edit, name="edit"),
    path("post/<slug:slug>/delete/", views.post_delete, name="delete"),
    path("post/<slug:slug>/comment/", views.comment_add, name="comment_add"),
    path("post/<slug:slug>/like/", views.like_toggle, name="like"),
]
