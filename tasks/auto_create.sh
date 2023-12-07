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
git checkout old-insta-rk
git pull old-insta-rk

# setup database

python manage.py delete_avd
python manage.py create_accounts -n=10000 