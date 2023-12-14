# project path
export CURRENT_DIR=`dirname $(readlink -f $0)`
export PRJ_DIR=`dirname $CURRENT_DIR`
# go to project root directory
cd $PRJ_DIR
#. ./tasks/environment.sh
# . tasks/environment.sh

# Kill python and AVD process
killall -9 python qemu-system-x86_64

# activate the virtual environment for python
#. env/bin/activate
. env/bin/activate

# update code
# git checkout old-insta-rk
git stash
git pull 

# setup database

python manage.py update_csv 
python manage.py delete_avd 
python manage.py on_pc --no_vpn --account_creation=True