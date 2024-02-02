# project path
export CURRENT_DIR=`dirname $(readlink -f $0)`
export PRJ_DIR=`dirname $CURRENT_DIR`
# go to project root directory
cd $PRJ_DIR
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

# update code
git checkout old-insta-rk
git stash
git pull 


# chmod +x tasks/install_missing_modules.sh
# . tasks/install_missing_modules.sh
# Add the missing module
echo "Checking if djangorestframework is installed..."
if ! python -c "import djangorestframework" 2>/dev/null; then
    echo "djangorestframework is missing. Installing..."
    pip install djangorestframework
else
    echo "djangorestframework is already installed."
fi

while IFS= read -r line; do
    module=$(echo $line | cut -d ' ' -f 2)
    echo "Checking if $module is installed..."
    if ! python -c "import $module" 2>/dev/null; then
        echo "$module is missing. Installing..."
        pip install $module
    else
        echo "$module is already installed."
    fi
done < <(python manage.py test 2>&1 | grep "No module named")
# setup database
# python temp/z22.py
python manage.py update_csv 
python manage.py delete_avd 
python manage.py on_pc --account_creation=True