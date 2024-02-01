import subprocess,os, time, json
from django.core.management.base import BaseCommand
from twbot.models import run_command
from dotenv import load_dotenv
load_dotenv()
class Command(BaseCommand):
    
    def handle(self, *args, **options):
        
        pcname = os.environ.get("SYSTEM_NO")
        
        commandss = run_command.objects.all()
        for cmd in commandss :
            comnd = cmd.command
            pcs = json.loads(cmd.pcs_name)
            breakpoint()