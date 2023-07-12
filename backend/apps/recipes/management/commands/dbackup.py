from datetime import datetime

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    def handle(self, *args, **options):
        call_command(
            'dumpdata',
            f'--output=db-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
        )
