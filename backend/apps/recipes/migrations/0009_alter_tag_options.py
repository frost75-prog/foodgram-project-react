# Generated by Django 4.2.2 on 2023-07-09 16:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_alter_shoppingcart_managers'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tag',
            options={'default_related_name': 'tags', 'ordering': ('id',), 'verbose_name': 'Тег', 'verbose_name_plural': 'Теги'},
        ),
    ]