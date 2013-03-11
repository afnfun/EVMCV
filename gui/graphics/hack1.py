import os
import string

name1="ballot-mockup3.png"
name2="ballot-mockup35.png"
name3="ballot-mockupx.png"
fullname1 = os.path.join('graphics', name1)
fullname2 = os.path.join('graphics', name2)
fullname3 = os.path.join('graphics', name3)
os.rename(fullname1,fullname3)
os.rename(fullname2,fullname1)
os.rename(fullname3,fullname2)

        
