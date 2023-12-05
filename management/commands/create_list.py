import sys
import time, os
from concurrent import futures
from xml.dom import UserDataHandler

import numpy as np
from django.core.management.base import BaseCommand

from conf import US_TIMEZONE, PARALLEL_NUMER
from core.models import User, user_detail
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.actions.follow import *
from twbot.bot import *


AGENT='xanametaverse'

class Command(BaseCommand):
    def handle(self, *args, **options): 
        active = []
        all_users = list(user_detail.objects.using('monitor').filter(status='ACTIVE').all())
        print(len(all_users),'-----')
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        print(len(avd_list))
        inactive = []
        for userr in all_users:
            # breakpoint()
            # breakpoint()
            # if not UserAvd.objects.filter(name = userr.avdsname).exists():
            #     user_avd = self.create_avd_object(userr.avdsname)
            if delete_local_avd_list.objects.filter(avdsname= userr.avdsname).exists():
                continue
            else:
                # user_avd = UserAvd.objects.filter(name=userr.avdsname).first()
                # random.shuffle(avd_list)
                # f = open('avd_list')
                # f.write(avd_list)
                # print(avd_list)
            
                if  userr.avdsname in avd_list:
                    # breakpoint()
                    avdname = userr.avdsname
                    if not UserAvd.objects.filter(name=userr.avdsname).first():
                        LOGGER.debug('Start to creating AVD user')
        
                        ports = list(
                                filter(
                                    lambda y: not UserAvd.objects.filter(port=y).exists(),
                                    map(
                                        lambda x: 5550 + x, range(1, 4000)
                                    )
                                )
                            )
                        
                        port = random.choice(ports)

                        country = 'Hong Kong'
                        LOGGER.debug(f'country: {country}')
                        if 'united states' in country.lower():
                            user_avd = UserAvd.objects.create(
                                user=User.objects.all().first(),
                                name=avdname,
                                port=port,
                                proxy_type="CYBERGHOST",
                                country=country,
                                timezone=random.choice(US_TIMEZONE),
                            )
                        else:
                            user_avd = UserAvd.objects.create(
                                user=User.objects.all().first(),
                                name=avdname,
                                port=port,
                                proxy_type="CYBERGHOST",
                                country=country
                            )

                        LOGGER.debug(f'AVD USER: {user_avd}')
                        
                        
                        LOGGER.info(f"**** AVD created with name2222: {avdname} ****")
                    else:
                        user_avd = UserAvd.objects.filter(name=userr.avdsname).first()
                        active.append(userr.avdsname)
                        
                    # UserAvd.objects.filter(name=userr.avdsname).first().delete()
                    # print(user_avd.name,'======================================')
                    # print(avd_list)
                else:
                    continue
            # LOGGER.info(f'{userr} -------11111')
        print(len(active))
        print(len(inactive))
