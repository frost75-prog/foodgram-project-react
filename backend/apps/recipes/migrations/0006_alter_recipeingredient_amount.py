# Generated by Django 4.2.2 on 2023-07-08 11:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_alter_shoppingcart_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.DecimalField(decimal_places=1, max_digits=7, validators=[django.core.validators.MinValueValidator(0.1, message='Минимальное количество ингридиентов - 0,1')], verbose_name='Количество'),
        ),
    ]
