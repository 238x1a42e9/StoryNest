import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Comment, ContactMessage, Post, Subscriber, Tag, render_markdown

User = get_user_model()


def make_author(username="maya"):
    user = User.objects.create_user(username, f"{username}@example.com", "pw-12345-x")
    user.groups.add(Group.objects.get(name="Authors"))
    return user


def make_post(author, title="Hello world", status=Post.PUBLISHED, **kw):
    return Post.objects.create(title=title, content="Some **content** here.", author=author, status=status, **kw)


class ModelTests(TestCase):
    def setUp(self):
        self.author = make_author()

    def test_slug_generated_and_unique(self):
        a = make_post(self.author, "Same title")
        b = make_post(self.author, "Same title")
        self.assertEqual(a.slug, "same-title")
        self.assertEqual(b.slug, "same-title-2")

    def test_markdown_is_sanitised(self):
        html = str(render_markdown("hi <script>alert(1)</script> [x](javascript:alert(1))"))
        self.assertNotIn("<script", html)
        self.assertNotIn("javascript:", html)

    def test_reading_time_minimum_one_minute(self):
        self.assertEqual(make_post(self.author).reading_minutes, 1)

    def test_summary_falls_back_to_content(self):
        self.assertIn("content", make_post(self.author).summary)


class ReadingTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.cat = Category.objects.create(name="Email")
        self.tag = Tag.objects.create(name="seo")
        self.post = make_post(self.author, "Open rates", category=self.cat)
        self.post.tags.add(self.tag)
        self.draft = make_post(self.author, "Secret draft", status=Post.DRAFT)

    def test_home_lists_published_only(self):
        r = self.client.get(reverse("blog:home"))
        self.assertContains(r, "Open rates")
        self.assertNotContains(r, "Secret draft")

    def test_detail_by_slug(self):
        r = self.client.get(f"/post/{self.post.slug}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Open rates")

    def test_draft_hidden_from_public_but_visible_to_author(self):
        url = self.draft.get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.login(username="maya", password="pw-12345-x")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_draft_hidden_from_other_users(self):
        User.objects.create_user("sam", "s@example.com", "pw-12345-x")
        self.client.login(username="sam", password="pw-12345-x")
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)

    def test_category_and_tag_filters(self):
        self.assertContains(self.client.get(self.cat.get_absolute_url()), "Open rates")
        self.assertContains(self.client.get(self.tag.get_absolute_url()), "Open rates")
        other = Category.objects.create(name="Other")
        self.assertNotContains(self.client.get(other.get_absolute_url()), "Open rates")

    def test_search(self):
        r = self.client.get("/search/", {"q": "rates"})
        self.assertContains(r, self.post.get_absolute_url())
        self.assertContains(r, "<mark>rates</mark>")  # matches are highlighted
        self.assertContains(self.client.get("/search/", {"q": "seo"}), self.post.get_absolute_url())
        self.assertContains(self.client.get("/search/", {"q": "zzzz"}), "No posts match")
        self.assertNotContains(self.client.get("/search/", {"q": "Secret"}), "Secret draft")

    def test_search_escapes_html(self):
        r = self.client.get("/search/", {"q": "<script>x</script>"})
        self.assertNotContains(r, "<script>x</script>")

    def test_related_posts_shown(self):
        other = make_post(self.author, "Related one", category=self.cat)
        r = self.client.get(self.post.get_absolute_url())
        self.assertContains(r, "Related one")
        self.assertContains(r, "Keep reading")
        self.assertEqual(other.category, self.cat)

    @override_settings(POSTS_PER_PAGE=2)
    def test_pagination(self):
        for i in range(5):
            make_post(self.author, f"Extra {i}")
        r = self.client.get("/blog/", {"page": 2})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Page 2 of")


class AuthTests(TestCase):
    def setUp(self):
        self.reader = User.objects.create_user("sam", "s@example.com", "pw-12345-x")
        self.author = make_author()

    def test_registration_creates_reader_by_default(self):
        r = self.client.post("/accounts/register/", {
            "username": "newbie", "email": "n@example.com",
            "password1": "a-strong-pass-77", "password2": "a-strong-pass-77",
        })
        self.assertEqual(r.status_code, 302)
        user = User.objects.get(username="newbie")
        self.assertFalse(user.has_perm("blog.add_post"))

    def test_registration_as_author(self):
        self.client.post("/accounts/register/", {
            "username": "writer", "email": "w@example.com",
            "password1": "a-strong-pass-77", "password2": "a-strong-pass-77", "wants_to_write": "on",
        })
        self.assertTrue(User.objects.get(username="writer").has_perm("blog.add_post"))

    def test_duplicate_email_rejected(self):
        r = self.client.post("/accounts/register/", {
            "username": "other", "email": "S@example.com",
            "password1": "a-strong-pass-77", "password2": "a-strong-pass-77",
        })
        self.assertContains(r, "already exists")
        self.assertFalse(User.objects.filter(username="other").exists())

    def test_login_and_logout(self):
        self.assertTrue(self.client.login(username="sam", password="pw-12345-x"))
        r = self.client.post("/accounts/logout/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get("/my-posts/").status_code, 302)

    def test_protected_pages_redirect_anonymous(self):
        post = make_post(self.author)
        for url in ["/write/", "/my-posts/", f"/post/{post.slug}/edit/", f"/post/{post.slug}/delete/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/accounts/login/", r["Location"])

    def test_reader_cannot_write(self):
        self.client.login(username="sam", password="pw-12345-x")
        self.assertEqual(self.client.get("/write/").status_code, 403)


class WritingTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.other = make_author("rival")
        self.client.login(username="maya", password="pw-12345-x")

    def data(self, **extra):
        base = {"title": "My first post", "content": "Body text", "status": "published",
                "tag_list": "SEO, email,  seo ", "new_category": "Planning"}
        base.update(extra)
        return base

    def test_create_post_with_new_category_and_tags(self):
        r = self.client.post("/write/", self.data())
        post = Post.objects.get(title="My first post")
        self.assertRedirects(r, post.get_absolute_url())
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.category.name, "Planning")
        self.assertEqual(sorted(post.tags.values_list("name", flat=True)), ["email", "seo"])

    def test_create_requires_title_and_content(self):
        r = self.client.post("/write/", self.data(title="", content=""))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

    def test_too_many_tags_rejected(self):
        r = self.client.post("/write/", self.data(tag_list=",".join(f"t{i}" for i in range(9))))
        self.assertContains(r, "at most 8 tags")

    def test_upload_cover(self):
        from io import BytesIO
        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (4, 4), "blue").save(buf, "PNG")
        png = buf.getvalue()
        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            r = self.client.post("/write/", self.data(cover=SimpleUploadedFile("c.png", png, "image/png")))
            self.assertEqual(r.status_code, 302)
            self.assertTrue(Post.objects.get(title="My first post").cover.name.endswith(".png"))

    def test_non_image_cover_rejected(self):
        r = self.client.post("/write/", self.data(cover=SimpleUploadedFile("c.txt", b"hello", "text/plain")))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

    def test_edit_own_post(self):
        post = make_post(self.author)
        r = self.client.post(f"/post/{post.slug}/edit/", self.data(title="Renamed"))
        self.assertEqual(r.status_code, 302)
        post.refresh_from_db()
        self.assertEqual(post.title, "Renamed")

    def test_cannot_edit_or_delete_someone_elses_post(self):
        post = make_post(self.other)
        self.assertEqual(self.client.get(f"/post/{post.slug}/edit/").status_code, 403)
        self.assertEqual(self.client.post(f"/post/{post.slug}/delete/").status_code, 403)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_delete_needs_post_and_removes(self):
        post = make_post(self.author)
        self.assertContains(self.client.get(f"/post/{post.slug}/delete/"), "Delete this post?")
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        self.client.post(f"/post/{post.slug}/delete/")
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_my_posts_separates_drafts(self):
        make_post(self.author, "Live one")
        make_post(self.author, "Draft one", status=Post.DRAFT)
        r = self.client.get("/my-posts/")
        self.assertContains(r, "Drafts (1)")
        self.assertContains(r, "Published (1)")

    def test_preview_endpoint_sanitises(self):
        r = self.client.post("/write/preview/", {"content": "**hi** <script>x</script>"})
        html = r.json()["html"]
        self.assertIn("<strong>hi</strong>", html)
        self.assertNotIn("<script", html)


class InteractionTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.reader = User.objects.create_user("sam", "s@example.com", "pw-12345-x")
        self.post = make_post(self.author)

    def test_anonymous_cannot_comment_or_like(self):
        for name in ("comment_add", "like"):
            r = self.client.post(reverse(f"blog:{name}", args=[self.post.slug]), {"text": "hi there"})
            self.assertEqual(r.status_code, 302)
            self.assertIn("/accounts/login/", r["Location"])
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(self.post.likes.count(), 0)

    def test_comment_flow(self):
        self.client.login(username="sam", password="pw-12345-x")
        self.client.post(f"/post/{self.post.slug}/comment/", {"text": "Great post"})
        self.assertEqual(self.post.comments.get().user, self.reader)
        self.assertContains(self.client.get(self.post.get_absolute_url()), "Great post")

    def test_comment_too_short_rejected(self):
        self.client.login(username="sam", password="pw-12345-x")
        self.client.post(f"/post/{self.post.slug}/comment/", {"text": " a "})
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_html_is_escaped(self):
        self.client.login(username="sam", password="pw-12345-x")
        self.client.post(f"/post/{self.post.slug}/comment/", {"text": "<b>bold</b> text"})
        r = self.client.get(self.post.get_absolute_url())
        self.assertContains(r, "&lt;b&gt;bold&lt;/b&gt; text")

    def test_comment_delete_permissions(self):
        c = Comment.objects.create(post=self.post, user=self.reader, text="mine")
        stranger = User.objects.create_user("eve", "e@example.com", "pw-12345-x")
        self.client.login(username="eve", password="pw-12345-x")
        self.assertEqual(self.client.post(f"/comment/{c.pk}/delete/").status_code, 403)
        self.client.login(username="maya", password="pw-12345-x")  # post author may moderate
        self.assertEqual(self.client.post(f"/comment/{c.pk}/delete/").status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=c.pk).exists())
        self.assertIsNotNone(stranger)

    def test_like_toggle_ajax(self):
        self.client.login(username="sam", password="pw-12345-x")
        url = f"/post/{self.post.slug}/like/"
        r = self.client.post(url, headers={"x-requested-with": "XMLHttpRequest"})
        self.assertEqual(r.json(), {"liked": True, "count": 1})
        r = self.client.post(url, headers={"x-requested-with": "XMLHttpRequest"})
        self.assertEqual(r.json(), {"liked": False, "count": 0})

    def test_like_requires_post_method(self):
        self.client.login(username="sam", password="pw-12345-x")
        self.assertEqual(self.client.get(f"/post/{self.post.slug}/like/").status_code, 405)

    def test_cannot_comment_on_someone_elses_draft(self):
        draft = make_post(self.author, "Hidden", status=Post.DRAFT)
        self.client.login(username="sam", password="pw-12345-x")
        r = self.client.post(f"/post/{draft.slug}/comment/", {"text": "peeking"})
        self.assertEqual(r.status_code, 404)


class SitePagesTests(TestCase):
    def setUp(self):
        self.author = make_author()
        for i in range(7):
            make_post(self.author, f"Story number {i}")

    def test_home_splits_latest_and_archive(self):
        r = self.client.get("/")
        self.assertEqual(len(r.context["latest"]), 3)
        self.assertEqual(len(r.context["archive"]), 3)
        self.assertContains(r, "Latest posts")
        self.assertContains(r, "From the archive")
        self.assertContains(r, "Stay in the loop")
        self.assertContains(r, "Hi, I&rsquo;m Rosie")
        self.assertContains(r, "Life, Styled by Rosie")

    def test_site_name_everywhere(self):
        r = self.client.get("/")
        self.assertContains(r, "StoryNest")
        self.assertNotContains(r, "Margin")

    def test_blog_index_lists_all_published(self):
        make_post(self.author, "Not public", status=Post.DRAFT)
        r = self.client.get("/blog/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Not public")
        self.assertContains(r, "Story number 6")

    def test_empty_home(self):
        Post.objects.all().delete()
        self.assertContains(self.client.get("/"), "Nothing published yet")

    def test_static_pages(self):
        for url in ["/privacy/", "/accessibility/", "/contact/", "/subscribe/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_contact_form_saves_message(self):
        r = self.client.post("/contact/", {"name": "Ann", "email": "ann@example.com", "message": "Hello there, lovely blog!"})
        self.assertRedirects(r, "/contact/")
        self.assertEqual(ContactMessage.objects.get().name, "Ann")

    def test_contact_form_validates(self):
        r = self.client.post("/contact/", {"name": "", "email": "nope", "message": "hi"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_subscribe_saves_and_ignores_duplicates(self):
        for _ in range(2):
            self.client.post("/subscribe/join/", {"email": "Fan@Example.com"})
        self.assertEqual(Subscriber.objects.count(), 1)
        self.assertEqual(Subscriber.objects.get().email, "fan@example.com")

    def test_subscribe_rejects_bad_email(self):
        self.client.post("/subscribe/join/", {"email": "not-an-email"})
        self.assertEqual(Subscriber.objects.count(), 0)

    def test_subscribe_get_not_allowed(self):
        self.assertEqual(self.client.get("/subscribe/join/").status_code, 405)

    def test_subscribe_redirect_is_safe(self):
        r = self.client.post("/subscribe/join/", {"email": "a@example.com", "next_page": "https://evil.example/"})
        self.assertEqual(r["Location"], "/")
