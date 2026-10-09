from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CommentForm, ContactForm, PostForm, SubscribeForm
from .models import Category, Comment, Post, Subscriber, Tag, render_markdown

User = get_user_model()


def _listing_queryset(request):
    return (
        Post.objects.visible_to(request.user)
        .filter(status=Post.PUBLISHED)
        .select_related("author", "category")
        .prefetch_related("tags")
        .annotate(n_comments=Count("comments", distinct=True), n_likes=Count("likes", distinct=True))
        .order_by("-created_at", "-pk")
    )


def _paginate(request, queryset):
    page = Paginator(queryset, settings.POSTS_PER_PAGE).get_page(request.GET.get("page"))
    return page


def _sidebar():
    return {
        "categories": Category.objects.annotate(
            n=Count("posts", filter=Q(posts__status=Post.PUBLISHED))
        ).filter(n__gt=0),
        "tags": Tag.objects.annotate(
            n=Count("posts", filter=Q(posts__status=Post.PUBLISHED))
        ).filter(n__gt=0).order_by("-n", "name")[:18],
    }


def home(request):
    posts = list(_listing_queryset(request)[:6])
    return render(request, "blog/home.html", {
        "latest": posts[:3],
        "archive": posts[3:6],
        "subscribe_form": SubscribeForm(),
        "has_posts": bool(posts),
    })


def blog_index(request):
    page = _paginate(request, _listing_queryset(request))
    return render(request, "blog/listing.html", {
        "page": page, "heading": "Blog", "kind": "blog", **_sidebar(),
    })


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    if form.is_valid():
        Subscriber.objects.get_or_create(email=form.cleaned_data["email"])
        messages.success(request, "You are on the list. Watch your inbox for the next note.")
    else:
        messages.error(request, " ".join(form.errors.get("email", ["Enter a valid email address."])))
    target = request.POST.get("next_page", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect("blog:home")


def privacy(request):
    return render(request, "blog/privacy.html")


def accessibility(request):
    return render(request, "blog/accessibility.html")


def subscribe_page(request):
    return render(request, "blog/subscribe.html", {"form": SubscribeForm()})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks. Your message is on its way and you will hear back soon.")
        return redirect("blog:contact")
    return render(request, "blog/contact.html", {"form": form})


def category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    page = _paginate(request, _listing_queryset(request).filter(category=category))
    return render(request, "blog/listing.html", {
        "page": page, "heading": category.name, "kind": "category", "active_category": category,
        **_sidebar(),
    })


def tag_list(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    page = _paginate(request, _listing_queryset(request).filter(tags=tag))
    return render(request, "blog/listing.html", {
        "page": page, "heading": f"Tagged {tag.name}", "kind": "tag", "active_tag": tag,
        **_sidebar(),
    })


def author_posts(request, username):
    author = get_object_or_404(User, username=username)
    page = _paginate(request, _listing_queryset(request).filter(author=author))
    return render(request, "blog/listing.html", {
        "page": page, "heading": f"Posts by {author.get_username()}", "kind": "author",
        **_sidebar(),
    })


def search(request):
    q = " ".join(request.GET.get("q", "").split())
    posts = _listing_queryset(request).none()
    if q:
        posts = _listing_queryset(request).filter(
            Q(title__icontains=q)
            | Q(content__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(tags__name__icontains=q)
            | Q(category__name__icontains=q)
        ).distinct()
    page = _paginate(request, posts)
    return render(request, "blog/search.html", {"page": page, "q": q, **_sidebar()})


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.visible_to(request.user).select_related("author", "category").prefetch_related("tags"),
        slug=slug,
    )
    comments = post.comments.select_related("user")
    tag_ids = list(post.tags.values_list("id", flat=True))
    related = (
        Post.objects.published()
        .exclude(pk=post.pk)
        .filter(Q(tags__in=tag_ids) | Q(category=post.category) if post.category_id else Q(tags__in=tag_ids))
        .annotate(shared=Count("tags", filter=Q(tags__in=tag_ids), distinct=True))
        .order_by("-shared", "-created_at")
        .distinct()[:3]
    )
    liked = request.user.is_authenticated and post.likes.filter(pk=request.user.pk).exists()
    return render(request, "blog/detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": CommentForm(),
        "related": related,
        "liked": liked,
        "like_count": post.likes.count(),
        "can_edit": post.author_id == getattr(request.user, "pk", None) or request.user.is_superuser,
    })


# ------------------------------------------------------------------ Writing
@login_required
@permission_required("blog.add_post", raise_exception=True)
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        form.save_tags(post)
        messages.success(request, "Published." if post.is_published else "Draft saved.")
        return redirect(post)
    return render(request, "blog/post_form.html", {"form": form, "mode": "create"})


def _owned_post_or_403(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.author_id != request.user.pk and not request.user.is_superuser:
        raise PermissionDenied
    return post


@login_required
def post_edit(request, slug):
    post = _owned_post_or_403(request, slug)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        post = form.save()
        messages.success(request, "Changes saved.")
        return redirect(post)
    return render(request, "blog/post_form.html", {"form": form, "mode": "edit", "post": post})


@login_required
def post_delete(request, slug):
    post = _owned_post_or_403(request, slug)
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect("blog:my_posts")
    return render(request, "blog/post_confirm_delete.html", {"post": post})


@login_required
def my_posts(request):
    posts = (
        Post.objects.filter(author=request.user)
        .select_related("category")
        .annotate(n_comments=Count("comments", distinct=True), n_likes=Count("likes", distinct=True))
        .order_by("-created_at", "-pk")
    )
    return render(request, "blog/my_posts.html", {
        "drafts": [p for p in posts if not p.is_published],
        "published": [p for p in posts if p.is_published],
    })


@require_POST
@login_required
def markdown_preview(request):
    return JsonResponse({"html": str(render_markdown(request.POST.get("content", "")))})


# -------------------------------------------------------- Comments and likes
@require_POST
@login_required
def comment_add(request, slug):
    post = get_object_or_404(Post.objects.visible_to(request.user), slug=slug)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post, comment.user = post, request.user
        comment.save()
        messages.success(request, "Comment added.")
    else:
        messages.error(request, " ".join(form.errors.get("text", ["Your comment could not be saved."])))
    return redirect(f"{post.get_absolute_url()}#comments")


@require_POST
@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=pk)
    allowed = request.user in (comment.user, comment.post.author) or request.user.is_superuser
    if not allowed:
        raise PermissionDenied
    post = comment.post
    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect(f"{post.get_absolute_url()}#comments")


@require_POST
@login_required
def like_toggle(request, slug):
    post = get_object_or_404(Post.objects.visible_to(request.user), slug=slug)
    if post.likes.filter(pk=request.user.pk).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "count": post.likes.count()})
    return redirect(post)
