import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def highlight(text, query):
    """Wrap case-insensitive matches of `query` in <mark>. Output is escaped first."""
    escaped = conditional_escape(text)
    query = (query or "").strip()
    if not query:
        return escaped
    pattern = re.compile(re.escape(conditional_escape(query)), re.IGNORECASE)
    return mark_safe(pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", str(escaped)))


@register.simple_tag(takes_context=True)
def page_url(context, number):
    """Current URL with ?page=<number>, keeping any other query parameters."""
    params = context["request"].GET.copy()
    params["page"] = number
    return "?" + params.urlencode()
