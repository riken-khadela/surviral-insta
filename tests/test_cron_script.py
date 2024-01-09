import subprocess

def check_cronjob(script_name):
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        output = result.stdout
        if script_name in output:
            print(f"The cron job for '{script_name}' is running.")
        else:
            print(f"The cron job for '{script_name}' is not currently running.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Replace 'your_script.sh' with your actual script's name
check_cronjob('your_script.sh')
