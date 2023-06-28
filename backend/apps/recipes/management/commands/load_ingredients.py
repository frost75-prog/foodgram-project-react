import csv

from django.core.management.base import BaseCommand
from progress.bar import IncrementalBar

from foodgram.settings import BASE_DIR
from apps.recipes.models import Ingredient


class Command(BaseCommand):
    """Load ingredients to DB"""

    FILE = 'data/ingredients.csv'

    def handle(self, *args, **kwargs):
        path = BASE_DIR / self.FILE
        total = 0
        with open(path, 'r', encoding='utf-8') as file:
            progress_bar = IncrementalBar(
                self.FILE.ljust(10), max=len(file.readlines()))
        with open(path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                progress_bar.next()
                _, created = Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1])
                if created:
                    total += 1
            progress_bar.finish()
        self.stdout.write(f'Created total: {total}')
