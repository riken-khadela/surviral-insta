from django.core.management.base import BaseCommand
import pandas as pd, os, subprocess
from django.core.management import call_command
from etc.local_bot import InstaBot
class Command(BaseCommand):

    def handle(self, *args, **options):
        bot = InstaBot(emulator_name='bhavin')
        bot.check_apk_installation()
        breakpoint()
        bot.connect_urban()