import datetime
import random
from flask_app.models import Accounts
def accgen():
    while(True):
        dt = datetime.datetime.now()
        acc = int(dt.strftime("%y%f")+str(random.randrange(10000000, 99999999)))
        pre = Accounts.query.filter(Accounts.accno==acc).first()
        if pre is None:
            break
    return acc

def trpingen():
    return random.randrange(10000, 99999)

def withdepid(amt):
    pin=""
    for _ in range(3):
        ch = chr(random.choice([random.randrange(65, 90), random.randrange(97,122), random.randrange(48,57)]))
        pin += ch
    amt *= random.randrange(random.randrange(200, 450), random.randrange(600,900))
    pin += str(amt)[3:0:-1]
    return pin

def accdis(accno):
    form = ''
    for i in range (1, 17):
        form = form + accno[i-1]
        if i%4==0 and i != 16:
            form = form + "-"
    return form