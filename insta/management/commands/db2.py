from django.core.management.base import BaseCommand
from insta.models import UserAvd as ud1
import pandas as pd

class Command(BaseCommand):
    def handle(self, *args, **options):
        breakpoint()
        df = pd.read_csv('/home/dell/Desktop/surviral-insta/useravds_twbot,csv')
        # for user in all_old_user :
        for idx,row in df.iterrows() : 
            print(row['id'])
            # ud1.objects.get_or_create(avdsname = user.avdsname,username = user.username,number = user.number,password = user.password,birth_date = user.birth_date,birth_month = user.birth_month,birth_year = user.birth_year,updated = user.updated,random_action = user.random_action,engagement = user.engagement,status = user.status,following = user.following,followers = user.followers,can_search = user.can_search,avd_pc = user.avd_pc,created_at = user.created_at,updated_at = user.updated_at,is_filtered = user.is_filtered,bio = user.bio,is_bio_updated = user.is_bio_updated)

            ud1.objects.create(id = row['id'],
                                name=row['name'],
                               port = row['port'],
                               proxy_type = row['proxy_type'],
                               country = "Hong Kong",
                               )