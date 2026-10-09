# StoryNest: a personal blog in Django

Readers browse, comment and like. The author writes, publishes and manages posts. Built with Python, Django, SQL (SQLite by default) and HTML/CSS/JavaScript.

## Run it

```
python -m venv .venv
.venv\Scripts\activate             (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000. Already have an older copy running? Use `python manage.py seed_demo --reset` to replace the old demo posts.

Demo logins (password for both: `storynest-demo-1`):

| User | Role | Can do |
|------|------|--------|
| `rosie` | Author | Write, edit, delete own posts, comment, like |
| `sam`   | Reader | Comment, like |

For the Django admin, run `python manage.py createsuperuser` and open `/admin/`. Newsletter sign-ups and contact messages are listed there.

## Pages

| Page | URL |
|------|-----|
| Home: collage hero, Latest posts, About, Stay in the loop, From the archive | `/` |
| Blog (all posts, paginated) | `/blog/` |
| Post with slug URL, likes and comments | `/post/<slug>/` |
| Category and tag filters | `/category/<slug>/`, `/tag/<slug>/` |
| Search | `/search/?q=...` |
| Contact form | `/contact/` |
| Subscribe | `/subscribe/` |
| Privacy Policy, Accessibility Statement | `/privacy/`, `/accessibility/` |
| Write, edit, delete, My posts (authors only) | `/write/`, `/post/<slug>/edit/`, `/post/<slug>/delete/`, `/my-posts/` |
| Register, log in, log out | `/accounts/register/`, `/accounts/login/`, `/accounts/logout/` |

## What is built

| Requirement | Where |
|---|---|
| Create, edit, delete posts | Post form with Markdown toolbar and live preview; delete has a confirmation page |
| Categories and tags | Pick or create a category; tags typed as a comma list; filter pages |
| Comment section | Logged-in users comment; owners and the post author can delete |
| Registration and login | Django's built-in `User`; sign-up form can grant author rights |
| Post detail with slug URL | Unique slugs generated from titles |
| `login_required` on create/edit | Plus a permission check, so readers get a 403 |
| Roles (week 2) | Reader vs Author (group `Authors`, created by a migration); superuser can moderate |
| Search (week 3) | Title, text, summary, tags and category, with highlighted matches |
| File upload (week 3) | Cover image per post, type and 4 MB checked |
| Status workflow (week 3) | Draft or Published; drafts visible only to their author |
| Testing and docs (week 4) | 48 tests, this file |
| Bonus: like button | AJAX toggle, works without JavaScript too |
| Bonus: rich text editor | Markdown toolbar with sanitised live preview |
| Bonus: related posts | "Keep reading" on each post, ranked by shared tags |

## Customise it

Everything personal lives in `config/settings.py`: `SITE_NAME`, `SITE_TAGLINE`, `AUTHOR_NAME`, `FOOTER_STATEMENT` ("Life, Styled by Rosie"), `ABOUT_TEXT`, `NEWSLETTER_TEXT`, the footer phone, email and address, and social links. The contact details are placeholders, so replace them with your own.

Photos:
- `static/img/` holds the homepage images. Replace `rosie.jpg` with your own portrait (it is a neutral placeholder).
- Post cover images are uploaded per post in the editor. The demo covers are in `blog/demo_images/`.

Colours and fonts are variables at the top of `static/css/storynest.css`.
To allow only you to write posts, set `ALLOW_AUTHOR_SIGNUP = False` and add authors in `/admin/`.

## Database

```
Category(id, name, slug)
Tag(id, name, slug)
Post(id, title, slug, content, excerpt, author_id, category_id, cover, status, created_at, updated_at)
Post_tags(id, post_id, tag_id)          many-to-many
Post_likes(id, post_id, user_id)        many-to-many
Comment(id, post_id, user_id, text, created_at)
Subscriber(id, email, created_at)
ContactMessage(id, name, email, message, created_at, handled)
auth_user(...)                          Django built-in
```

See the SQL with `python manage.py sqlmigrate blog 0001`.

## Tests

```
python manage.py test
```

## Security notes

- Post text is sanitised (`nh3`) and comments are escaped before display.
- Delete, logout, like, comment, subscribe and preview accept POST only and use CSRF tokens.
- Before deploying: set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS`, run `python manage.py collectstatic`, and serve uploaded media from your web server.
- Fonts load from Google Fonts and fall back to system fonts offline.
