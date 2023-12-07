import subprocess, os
from dotenv import load_dotenv
load_dotenv()
old_pcs = ['pc3','pc8','pc11','pc20','pkpc16','pkpc17']

if os.getenv('PC') in old_pcs :
    
    breakpoint()