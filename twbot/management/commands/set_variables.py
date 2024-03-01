from django.core.management.base import BaseCommand, CommandError
import subprocess, os

class Command(BaseCommand):
    help = 'Runs a specified shell script'

    def handle(self, *args, **options):
        print(os.environ.get("SENDER_PASSWORD"))
        print(os.environ.get("RECEIVER_MAIL"))
        print(os.environ.get("SENDER_MAIL"))
        print(os.environ.get("SYSTEM_NO"))

