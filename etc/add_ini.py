import os

avd_root = os.path.expanduser('~/.android/avd')
            
def create_avd_ini():
    avd_root = os.path.expanduser('~/.android/avd')

    avd_folders = [filename for filename in os.listdir(avd_root) if filename.endswith('.avd')]

    for folder in avd_folders:
        folder_path = os.path.join(avd_root, folder)
        avd_name = os.path.basename(folder_path)
        ini_avd_name = str(avd_name).split('.')[0]
        avd_root = os.path.expanduser('~/.android/avd')
        ini_path = os.path.join(avd_root, ini_avd_name+'.ini')
        if not os.path.exists(ini_path):
            with open(ini_path, 'w') as ini_file:
                ini_file.write('avd.ini.encoding=UTF-8\n')
                ini_file.write('path=' + folder_path + '\n')
                ini_file.write(f'path.rel=avd/{ini_avd_name}.avd'+'\n')
                ini_file.write('target=android-28\n')
        # create_avd_ini(folder_path)
        print(f"Created INI file for AVD folder {folder_path}")


def delete_currupt_avd():
    import os

    # Path to the Android SDK
    ANDROID_SDK_ROOT = os.path.expanduser('~/.android')

    # Get the list of AVD names
    avd_list = os.popen('avdmanager list avd').read().splitlines()
    avd_list = [line.split(": ")[1] for line in avd_list if line.startswith("    Name: ")]

    # Iterate over the AVD list
    for avd_name in avd_list:
        avd_folder = os.path.join(ANDROID_SDK_ROOT, "avd", f"{avd_name}.avd")
        ini_file = os.path.join(avd_folder, "config.ini")

        # Check if INI file does not exist
        if not os.path.isfile(ini_file):
            print(f"INI file not found for AVD: {avd_name}")

            # Delete the AVD folder
            print(f"Deleting AVD folder: {avd_folder}")
            os.system(f"rm -rf {avd_folder}")

            print("AVD deleted successfully.")

# def delete_ini():
    # avd_list = os.popen('avdmanager list avd').read().splitlines()
    # avd_list = [line.split(": ")[1] for line in avd_list if line.startswith("    Name: ")]

    for folder in avd_list:
        folder_path = os.path.join(avd_root, f'{folder}.avd')
        ini_file = os.path.join(avd_root, f"{folder}.ini")

        if not os.path.isdir(folder_path):
            if os.path.isfile(ini_file):
                os.system(f"rm -rf {ini_file}")
                print(f"delete INI file for AVD ini {ini_file}")

delete_currupt_avd()