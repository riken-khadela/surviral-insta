import os, pandas as pd

# # Get the environment variable
# my_variable = os.environ.get('MY_VARIABLE')

# # Check if the variable exists
# if my_variable is not None:
#     print(f'The value of MY_VARIABLE is: {my_variable}')
# else:
#     print('The environment variable MY_VARIABLE is not set.')
# required_accounts = 1
# accounts_created = 0
# while accounts_created < required_accounts :
#     print(accounts_created)
#     accounts_created += 1
from datetime import datetime
df = pd.DataFrame()
csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
df = pd.read_csv(csv_path)  
breakpoint()
enged_date_times_li = [datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f%z') for dt in df['eng_at'].tolist()]
sorted_user_li = sorted(enged_date_times_li)
user_data_dict = df.to_dict(orient='records')
all_users = [user_data_dict[enged_date_times_li.index(user)] for user in sorted_user_li]

oldest_eng_date_idx = enged_date_times_li.index(min(enged_date_times_li))
