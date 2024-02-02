#!/bin/bash

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
