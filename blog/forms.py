from django import forms

from .models import Category, Comment, ContactMessage, Post, Subscriber, Tag

MAX_COVER_BYTES = 4 * 1024 * 1024


class PostForm(forms.ModelForm):
    """Create or edit a post. Tags are typed as a comma-separated list."""

    tag_list = forms.CharField(
        label="Tags",
        required=False,
        help_text="Separate tags with commas, for example: seo, email, launch.",
        widget=forms.TextInput(attrs={"placeholder": "seo, email, launch"}),
    )
    new_category = forms.CharField(
        label="New category",
        required=False,
        max_length=60,
        help_text="Type a name here to create a category instead of picking one.",
    )

    class Meta:
        model = Post
        fields = ["title", "category", "new_category", "tag_list", "cover", "excerpt", "content", "status"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 18, "id": "id_content"}),
            "excerpt": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {"status": "Visibility", "cover": "Cover image", "excerpt": "Summary"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["category"].empty_label = "No category"
        self.fields["status"].choices = [
            (Post.DRAFT, "Draft: only you can see it"),
            (Post.PUBLISHED, "Published: visible to everyone"),
        ]
        if self.instance.pk:
            self.fields["tag_list"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_cover(self):
        cover = self.cleaned_data.get("cover")
        if cover and hasattr(cover, "size") and cover.size > MAX_COVER_BYTES:
            raise forms.ValidationError("Cover images must be 4 MB or smaller.")
        return cover

    def clean_tag_list(self):
        raw = self.cleaned_data.get("tag_list", "")
        names, seen = [], set()
        for part in raw.split(","):
            name = " ".join(part.split()).lower()[:40]
            if name and name not in seen:
                seen.add(name)
                names.append(name)
        if len(names) > 8:
            raise forms.ValidationError("Use at most 8 tags per post.")
        return names

    def save(self, commit=True):
        post = super().save(commit=False)
        new_category = self.cleaned_data.get("new_category", "").strip()
        if new_category:
            post.category, _ = Category.objects.get_or_create(
                name__iexact=new_category, defaults={"name": new_category}
            )
        if commit:
            post.save()
            self.save_tags(post)
        return post

    def save_tags(self, post):
        tags = []
        for name in self.cleaned_data.get("tag_list", []):
            tag = Tag.objects.filter(name__iexact=name).first() or Tag.objects.create(name=name)
            tags.append(tag)
        post.tags.set(tags)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        labels = {"text": "Add a comment"}
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Say what you think. Be kind."})
        }

    def clean_text(self):
        text = self.cleaned_data["text"].strip()
        if len(text) < 2:
            raise forms.ValidationError("Write at least a couple of characters.")
        return text


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email"]
        labels = {"email": "Email address"}
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"})}

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    # Subscribing twice should not be an error; the view treats it as success.
    def validate_unique(self):
        pass


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        labels = {"name": "Your name", "email": "Email address", "message": "Message"}
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_message(self):
        text = self.cleaned_data["message"].strip()
        if len(text) < 10:
            raise forms.ValidationError("Write at least a sentence so we know how to help.")
        return text
