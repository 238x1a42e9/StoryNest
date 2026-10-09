"""Fill the blog with demo users, posts, comments and cover images.

    python manage.py seed_demo          # add demo data (safe to run twice)
    python manage.py seed_demo --reset  # delete all posts, categories and tags first
"""
from datetime import datetime, timezone as dt_tz
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from blog.models import Category, Comment, Post, Tag

IMAGES = Path(__file__).resolve().parents[2] / "demo_images"

CAPTION = (
    "When it comes to design, StoryNest has everything you need to create beautiful posts "
    "that will grab your reader's attention. Check out our essential design features. "
    "Choose from several beautiful layouts."
)

POSTS = [
    {
        "title": "Colour Is the Easiest Way to Warm a Room", "category": "Home", "cover": "art",
        "tags": ["decor", "colour"], "date": (2026, 3, 12),
        "content": """One large piece of art did more for my living room than any new sofa could.

## Start with a single shape

I propped a bold print against the wall before deciding where to hang it. Seeing it in place for a week told me more than any measuring tape.

- Pick one colour you already love and let it lead.
- Keep the surrounding walls quiet.
- Add a plant or dried stems for softness.

> A room feels finished when your eye has somewhere to rest.

## What I would do differently

Hang it lower than you think. Art belongs to the furniture beneath it, not to the ceiling.""",
    },
    {
        "title": "Three Days Above the Treeline", "category": "Travel", "cover": "mountain",
        "tags": ["travel", "hiking"], "date": (2026, 3, 5),
        "content": """We packed light, walked slowly and let the weather decide the plan.

## What went in the bag

1. A warm layer, even in summer
2. Far more snacks than seemed sensible
3. A paper map, just in case

## The part I remember

Not the summit. It was the long, quiet stretch of green valley on the second afternoon, when nobody felt like talking and nobody needed to.""",
    },
    {
        "title": "A Pantry Worth Showing Off", "category": "Home", "cover": "oils",
        "tags": ["kitchen", "organizing"], "date": (2026, 2, 28),
        "content": """Good ingredients deserve a good shelf. Mine now holds three bottles, a candle and nothing else I do not use weekly.

## The rules I follow

- Decant what you can into clear jars.
- Keep oils and vinegars within arm's reach of the stove.
- Light a candle when you cook. It makes a weeknight feel intentional.

Small habits, big difference.""",
    },
    {
        "title": "A Year of Slow Travel", "category": "Travel", "cover": "road",
        "tags": ["travel", "slow-living"], "date": (2026, 2, 25),
        "content": """Last year I took fewer trips and stayed longer in each place. It changed how I travel.

## What staying longer gives you

- A favourite cafe, and a barista who knows your order
- Time to be bored, which is where the best ideas show up
- Money saved on flights, spent on better meals

## The road that stayed with me

A winding mountain road, a rented car and no schedule. We stopped whenever the view asked us to.""",
    },
    {
        "title": "How I Organize My Small Kitchen", "category": "Home", "cover": "jars",
        "tags": ["kitchen", "organizing"], "date": (2026, 2, 25),
        "content": """A small kitchen asks you to be honest about what you actually cook with.

## Five changes that worked

1. Matching jars for grains and pulses
2. One tall rack for boards and trays
3. Wooden spoons in a crock by the stove
4. Labels on everything, handwritten
5. A single vase of flowers, because why not

## The result

Everything has a home, and I can find it in the dark.""",
    },
    {
        "title": "The Capsule Wardrobe That Actually Works", "category": "Style", "cover": "shoes",
        "tags": ["style", "wardrobe"], "date": (2026, 2, 25),
        "content": """I tried a strict thirty-piece wardrobe and gave up in a week. This looser version has lasted.

## The loose rules

- Everything must go with at least three other things.
- One statement piece per season, like these green heels.
- If I have not worn it in a year, it goes.

## Why it works

Because it leaves room for a little joy. A wardrobe with no surprises is just a uniform.""",
    },
]

COMMENTS = [
    "This is so lovely. Saving it for later.",
    "Thanks for sharing the details, they really help.",
    "I tried this last weekend and it worked beautifully.",
]


class Command(BaseCommand):
    help = "Create demo users, categories, tags, posts, comments and likes."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all posts, categories and tags first.")

    def handle(self, *args, **options):
        assert len(CAPTION) <= 240, len(CAPTION)
        User = get_user_model()
        if options["reset"]:
            Post.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()

        authors = Group.objects.get(name="Authors")
        author, created = User.objects.get_or_create(username="rosie", defaults={"email": "rosie@example.com"})
        if created:
            author.set_password("storynest-demo-1")
            author.save()
        author.groups.add(authors)

        reader, created = User.objects.get_or_create(username="sam", defaults={"email": "sam@example.com"})
        if created:
            reader.set_password("storynest-demo-1")
            reader.save()

        made = 0
        for i, data in enumerate(POSTS):
            if Post.objects.filter(title=data["title"]).exists():
                continue
            category, _ = Category.objects.get_or_create(name=data["category"])
            y, m, d = data["date"]
            post = Post(
                title=data["title"], content=data["content"], excerpt=CAPTION, author=author,
                category=category, status=Post.PUBLISHED,
                created_at=datetime(y, m, d, 9, 30 - i, tzinfo=dt_tz.utc),
            )
            post.save()
            image = IMAGES / f"{data['cover']}.jpg"
            post.cover.save(f"{data['cover']}.jpg", ContentFile(image.read_bytes()), save=True)
            post.tags.set([Tag.objects.get_or_create(name=t)[0] for t in data["tags"]])
            if i % 2 == 0:
                post.likes.add(reader)
            for text in COMMENTS[: (i % 3) + 1]:
                Comment.objects.create(post=post, user=reader, text=text)
            made += 1

        self.stdout.write(self.style.SUCCESS(f"Created {made} posts."))
        self.stdout.write("Author login: rosie / storynest-demo-1")
        self.stdout.write("Reader login: sam / storynest-demo-1")
