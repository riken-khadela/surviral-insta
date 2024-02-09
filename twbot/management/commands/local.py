from django.core.management.base import BaseCommand
import pandas as pd, os, subprocess, sys
from django.core.management import call_command
from etc.local_bot import *
import psutil
class Command(BaseCommand):

    def handle(self, *args, **options):
        avdsname = 'bhavin'
        try:
            bot = InstaBot(emulator_name=avdsname)
            bot.check_apk_installation()
            vpn = bot.connect_urban('Hong Kong')
            bot.driver().activate_app('com.instagram.android')
            print(f'\n\nVpn is connnected : {vpn}\n\n')
            bot.clear_app_tray()
            breakpoint()
        finally:
            if 'bot' in locals() or 'bot' in globals():
                self.clean_bot(bot,is_sleep=False)
            else:
                name = avdsname
                port = ''
                parallel.stop_avd(name=name, port=port)

    def clean_bot(self, tb, is_sleep=True):
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(10, 20)