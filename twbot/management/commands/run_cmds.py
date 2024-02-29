import subprocess,os, time, json, signal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from twbot.models import run_command
from dotenv import load_dotenv
from maill import SendErrorMail

load_dotenv()
class Command(BaseCommand):
    
    def handle(self, *args, **options):
        pcname = os.environ.get("SYSTEM_NO")
        if not pcname: 
            SendErrorMail()
            return
        print('Test Pass')
        try:
            commandss = run_command.objects.filter(execute=False, pcs_name=pcname).order_by('created')
            for cmd in commandss:
                if cmd.pcs_name == pcname:
                    comnd = cmd.command
                    try:
                        result = subprocess.run([comnd], capture_output=True, text=True, check=True)
                        cmd.execute = True
                        cmd.save()
                    except subprocess.CalledProcessError as e:
                        SendErrorMail(body=f"Error in execution: {e}")
        except Exception as e:
            SendErrorMail(body=f"Error in execution: {e}")