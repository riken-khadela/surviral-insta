from twbot.models import TodayOpenAVD
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    # def add_arguments(self, parser):
    help = 'Clears the data of TodaysOpenAvd model at the end of each day'

    def handle(self, *args, **options):
        # Get the current date and time
        now = datetime.now()
        # Get the time at the end of the day (i.e. 23:59:59)
        end_of_day = datetime.combine(now.date(), time.max)
        # If the current time is after the end of the day
        if now > end_of_day:
            # Delete all records in the TodaysOpenAvd model
            TodayOpenAVD.objects.all().delete()
            # Print a message to the console
            self.stdout.write(self.style.SUCCESS('Successfully cleared the TodaysOpenAvd model data'))



