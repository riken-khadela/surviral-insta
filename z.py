import os

# Get the environment variable
my_variable = os.environ.get('MY_VARIABLE')

# Check if the variable exists
if my_variable is not None:
    print(f'The value of MY_VARIABLE is: {my_variable}')
else:
    print('The environment variable MY_VARIABLE is not set.')
