# project path
export CURRENT_DIR=`dirname $(readlink -f $0)`
export PRJ_DIR=`dirname $CURRENT_DIR`
# go to project root directory
cd $PRJ_DIR

# Check if variable.sh file exists
if [ ! -f "tasks/variable.sh" ]; then
    echo "Variable file not found. Running python3 create_task.py..."
    python3 create_task.py
fi

python3 cron_scheduler.py
# Replace the line in environment.sh
sed -i '/export LESSCLOSE=\/usr\/bin\/lesspipe %s %s/d' tasks/environment.sh


#. ./tasks/environment.sh
. tasks/environment.sh
. tasks/variable.sh

killall -9 python qemu-system-x86_64
# Kill python and AVD process
# export SENDER_PASSWORD='hfac mvld ecjx clru'
# export RECEIVER_MAIL="rikenkhadela22@gmail.com"
# export SENDER_MAIL='rikenkhadela777@gmail.com'
# export SYSTEM_NO='RK'
# activate the virtual environment for python
#. env/bin/activate
. env/bin/activate

sudo systemctl restart systemd-resolved

# update code
git checkout old-insta-rk
git stash
git pull 


# chmod +x tasks/install_missing_modules.sh
# . tasks/install_missing_modules.sh
# Add the missing module
python manage.py update_csv 2>&1 | grep "No module named" > /tmp/module_errors.txt
# Check if there are any errors
if [ -s /tmp/module_errors.txt ]; then
    # Process the temporary file
    while IFS= read -r line; do
        module=$(echo $line | cut -d ' ' -f 5 | tr -d "'")  # Remove single quotes

        # Map module names to correct package names
        case $module in
            "rest_framework") package_name="djangorestframework" ;;
            # Add more mappings as needed
            *) package_name="$module" ;;
        esac

        echo "Checking if $module is installed..."
        if ! python -c "import $module" 2>/dev/null; then
            echo "$module is missing. Installing $package_name..."
            pip install "$package_name"
        else
            echo "$module is already installed."
        fi
    done < /tmp/module_errors.txt

    # Cleanup the temporary file
    rm /tmp/module_errors.txt
else
    echo "No module errors found. Tests run successfully."
    # Add additional commands or actions here if needed
fi


# setup database
# python temp/z22.py
python manage.py update_csv
python manage.py delete_avd 
python manage.py on_pc --account_creation=True