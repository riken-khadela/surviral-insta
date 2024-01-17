from django.core.management.base import BaseCommand, CommandError
import subprocess, os
from main import LOGGER

class Command(BaseCommand):
    help = 'Runs a specified shell script'

    def handle(self, *args, **options):
        
        script_li = [
            os.path.join(os.getcwd(),'tasks','variable.sh')
        ]
        
        for sh_file in script_li :
            try:
                result = subprocess.run(['sh',sh_file], check=True, text=True, capture_output=True)
                self.stdout.write(self.style.SUCCESS(f'Successfully executed script: {sh_file}'))
                # self.stdout.write(result.stdout)
            except subprocess.CalledProcessError as e:
                LOGGER.error(e)
                raise CommandError('Error in script execution: %s' % e)
