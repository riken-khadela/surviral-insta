import datetime
import pytz
import os, tempfile
from utils import run_cmd
from main import LOGGER


class CronjobScheduler:
    def __init__(self, cron_time):
        self.cron_time = cron_time

    def check_system_time_ist(self):
        # Get the current system time
        current_time = datetime.datetime.now()

        # Get the current time in IST timezone
        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.datetime.now(ist_timezone)
        
        # Check if the hours and minutes match
        return current_time.hour == current_time_ist.hour and current_time.minute == current_time_ist.minute

    def calculate_time_difference(self):
        # Get the current time in IST timezone
        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.datetime.now(ist_timezone)

        # Get the current system time
        current_time = datetime.datetime.now()

        # Calculate the time difference in hours and minutes
        time_difference_hours = current_time_ist.hour - current_time.hour
        time_difference_minutes = current_time_ist.minute - current_time.minute

        # Return the time difference
        return time_difference_hours, time_difference_minutes

    def set_cronjob(self):
        # Calculate the time difference between IST and system time
        time_difference_hours, time_difference_minutes = self.calculate_time_difference()

        # Parse the cron_time variable to extract hours and minutes
        cron_time_parts = self.cron_time.split()
        cron_time_hour, cron_time_minute = map(int, cron_time_parts[0].split(':'))
        if len(cron_time_parts) > 1 and 'PM' in cron_time_parts[1].upper():
            cron_time_hour += 12

        # Adjust the cronjob time based on the time difference
        cronjob_hour = cron_time_hour - time_difference_hours
        cronjob_minute = cron_time_minute - time_difference_minutes

        # Set the cronjob using the adjusted time
        cronjob_time = f"{cronjob_minute} {cronjob_hour} * * *"
        # Replace this with your code to set the cronjob
        cmd = 'cron_job.sh'
        cmds = 'crontab -l'
        verbose = True
        result = run_cmd(cmds, verbose=verbose)
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_file_path = current_file_path.replace('/twbot/management/commands','')
        
        if result:
            (returncode, output) = result
            #  LOGGER.info(output)
            outs = output.strip().split('\n')
            outs_all = [e + '\n' for e in outs]
            effective_outs = [ e + '\n' for e in outs if not e.strip().startswith('#')]
            if 'no crontab for' in output:
                #  outs_all = ['\n']
                outs_all = []
                effective_outs = []
            exist_flag = False
            exist_job = ''
            for item in effective_outs:
                if cmd in item :
                    LOGGER.info(f'There has already been one job for command {cmd}')
                    exist_flag = True
                    exist_job = item
                    break
            
            if exist_flag:
                LOGGER.info(f'Override the existing job: {exist_job}')
                
                outs_all.remove(exist_job) if exist_job in outs_all else ...

                if exist_job.strip().startswith('@'):
                    if 'sleep' in exist_job:
                        LOGGER.info('The cron job starts with @ and with a command sleep, now ignore it')
                        return True
                
            new_job_parts = [cronjob_time, '/bin/bash',os.path.join(current_file_path,'tasks/cron_job.sh'), '>>', os.path.join(current_file_path,'tasks/cron_job.log'), '2>&1']
            new_job = ' '.join(new_job_parts) + '\n'
            LOGGER.info(f'New crontab job: {new_job}')
            
            outs_all.append(new_job)
            jobs_text = ''.join(outs_all)
            LOGGER.info(jobs_text)
            with tempfile.NamedTemporaryFile(mode='w+t') as fp:
                LOGGER.info(f'Write jobs to file {fp.name}')
                fp.write(jobs_text)
                fp.flush()
                # import crontab job
                cmds = f'crontab {fp.name}'
                verbose = True
                result = run_cmd(cmds, verbose=verbose)
                if result:
                    (returncode, output) = result
                    if returncode == 0:
                        LOGGER.info('Imported jobs into crontab')
                    else:
                        LOGGER.info('Failed to import jobs into crontab')
                else:
                    LOGGER.info('Cannot importe jobs into crontab')
                #  LOGGER.info(new_output)
        else:
            LOGGER.info('Cannot get crontab jobs')
        print(f"Set cronjob at {cronjob_time} in system time")

    def main(self):
        
        # Check if the PC is in India (IST timezone)
        if self.check_system_time_ist():
            print("The PC is in India. Setting cronjob as per provided time.")
            self.set_cronjob()
        else:
            print("The PC is not in India. Adjusting cronjob schedule based on the time difference.")
            self.set_cronjob()

# Example usage
if __name__ == "__main__":
    cron_time = "6:00 PM"
    cmds = 'crontab -l'
    result = run_cmd(cmds, verbose=True)
    scheduler = CronjobScheduler(cron_time)
    scheduler.main()




