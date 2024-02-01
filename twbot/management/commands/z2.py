import subprocess,os, time
from django.core.management.base import BaseCommand
from twbot.models import UserAvd,User_details
from dotenv import load_dotenv
load_dotenv()
class Command(BaseCommand):

    def append_text_to_file(self,file_path, text_to_append):
        """
        Appends text to a file.

        Parameters:
        - file_path (str): The path to the file.
        - text_to_append (str): The text to append to the file.
        """
        try:
            with open(file_path, 'a') as file:
                file.write(text_to_append + '\n')  # Appending text and adding a newline for clarity
            print(f"Text appended to {file_path} successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Example usage:

    
    def handle(self, *args, **options):
        file_path = 'example.txt'
        text_to_append = 'This is the text to append.'
        self.append_text_to_file(file_path, text_to_append)
        print('started command !')
        time.sleep(20)
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        print(avd_list)