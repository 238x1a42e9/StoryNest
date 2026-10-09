from django.conf import settings
from django.utils import timezone

from .models import Category


def site(request):
    """Expose site-wide values to every template."""
    user = getattr(request, "user", None)
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "AUTHOR_NAME": settings.AUTHOR_NAME,
        "FOOTER_STATEMENT": settings.FOOTER_STATEMENT,
        "ABOUT_TEXT": settings.ABOUT_TEXT,
        "NEWSLETTER_TEXT": settings.NEWSLETTER_TEXT,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "CONTACT_ADDRESS": settings.CONTACT_ADDRESS,
        "SOCIAL_LINKS": settings.SOCIAL_LINKS,
        "current_year": timezone.now().year,
        "nav_categories": Category.objects.all()[:8],
        "can_write": bool(user and user.is_authenticated and user.has_perm("blog.add_post")),
    }
