import sys
import time, os
from concurrent import futures
from xml.dom import UserDataHandler

import numpy as np, pandas as pd
from django.core.management.base import BaseCommand

from conf import US_TIMEZONE, PARALLEL_NUMER
from core.models import User , user_detail, EngageTask
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.actions.follow import *
from twbot.bot import *
from twbot.models import User_details

class Command(BaseCommand):
    def handle(self, *args, **options): 
        all_User = user_detail.objects.using('monitor').all()
        
        for user in all_User:
            aa = User_details.objects.update_or_create(
                avdsname = user.avdsname,
                username = user.username,
                number = user.number,
                password = user.password,
                birth_date = user.birth_date,
                birth_month = user.birth_month,
                birth_year = user.birth_year,
                updated = user.updated,
                random_action = user.random_action,
                status = user.status,
                following = user.following,
                followers = user.followers,
                avd_pc = user.avd_pc,
                

            )
            print(aa)