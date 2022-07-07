from datetime import datetime, time
from base.setting import settings
import re

if __name__ == "__main__":
    # a = set()
    # for i in settings.get("symbol.tradingtime").keys():
    #     a.add(i)

    # a = set(a)
    print(re.match("\D*", "RT22").group())
    print(datetime.now().time() < time(9,0))