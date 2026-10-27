from django.db import migrations

FACTORY_REPRESENTATIVE_GROUP = "Представитель ЗМК"
FACTORY_MANAGER_GROUP = "Менеджер по взаимодействию с ЗМК"
GROUP_NAMES = (FACTORY_REPRESENTATIVE_GROUP, FACTORY_MANAGER_GROUP)


def create_groups(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    for name in GROUP_NAMES:
        group_model.objects.using(schema_editor.connection.alias).get_or_create(name=name)


def delete_groups(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    group_model.objects.using(schema_editor.connection.alias).filter(name__in=GROUP_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("plan", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]
