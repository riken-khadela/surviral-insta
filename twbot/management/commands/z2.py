import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **options):
        my_variable = os.environ.get('MY_VARIABLE')
        print(my_variable)
    
        
        ...