# from django.test import TestCase

# Create your tests here.

from os import read
import pandas as pd


df = pd.read_csv('delete_avd.csv')
# df.loc['avd']='Avd-2'
df.drop(df.index[df['avd']== ''], axis=0,inplace=True)
df.to_csv('delete_avd.csv',index=False)
