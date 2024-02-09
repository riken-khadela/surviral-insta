from django.utils import timezone
from datetime import timedelta
import os
from twbot.models import User_details
from django.db.models import Q
from maill import SendErrorMail
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
load_dotenv()


class Command(BaseCommand):

    def handle(self, *args, **options):
        avd_pc = os.getenv('SYSTEM_NO')
        current_datetime = timezone.now()
        twenty_four_hours_ago = current_datetime - timedelta(hours=24)
        objects_created_last_24_hours = User_details.objects.filter(
                Q(created_at__gte=twenty_four_hours_ago) & Q(avd_pc=avd_pc)
            )        
        total_created_account = len(objects_created_last_24_hours)
        SendErrorMail(body=f"Today's created accounts on the {avd_pc} system is {total_created_account}.")