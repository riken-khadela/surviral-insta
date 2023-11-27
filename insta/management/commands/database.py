from twbot.models import User_details as ud2
from django.core.management.base import BaseCommand
from insta.models import User_details as ud1
class Command(BaseCommand):
    def handle(self, *args, **options):
        breakpoint()
        all_old_user = ud2.objects.using("monitor").all()
        for user in all_old_user :
            print(user.id)
            ud1.objects.get_or_create(avdsname = user.avdsname,username = user.username,number = user.number,password = user.password,birth_date = user.birth_date,birth_month = user.birth_month,birth_year = user.birth_year,updated = user.updated,random_action = user.random_action,engagement = user.engagement,status = user.status,following = user.following,followers = user.followers,can_search = user.can_search,avd_pc = user.avd_pc,created_at = user.created_at,updated_at = user.updated_at,is_filtered = user.is_filtered,bio = user.bio,is_bio_updated = user.is_bio_updated)

        ...