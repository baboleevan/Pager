from datetime import datetime

from pytz import timezone

KST = timezone('Asia/Seoul')

def now():
    return datetime.now(KST)