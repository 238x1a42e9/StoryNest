from django.db import migrations

AUTHORS = "Authors"
CODENAMES = [
    "add_post", "change_post", "delete_post", "view_post",
    "add_category", "change_category", "view_category",
    "add_tag", "change_tag", "view_tag",
]


def create_authors_group(apps, schema_editor):
    """Create the Authors group with the permissions needed to write posts."""
    from django.contrib.auth.management import create_permissions

    app_config = apps.get_app_config("blog")
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    group, _ = Group.objects.get_or_create(name=AUTHORS)
    group.permissions.set(
        Permission.objects.filter(content_type__app_label="blog", codename__in=CODENAMES)
    )


def remove_authors_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name=AUTHORS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("blog", "0001_initial"),
    ]
    operations = [migrations.RunPython(create_authors_group, remove_authors_group)]
