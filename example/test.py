# import os
# from database.mongodb import MongoDatabase
from datetime import datetime
import os, sys

if __name__ == "__main__":
    sys.path.append(os.getcwd())

    # engine = MainEngine()
    # bar_engine: BarEngine = engine.add_engine(BarEngine)
    # bar_engine.init(1, on_bar)

    # engine.connect()

    # contracts = engine.get_all_contracts()
    # a = "rB2210.SHFE"

    # print(re.match("\D*", a).group())
    date = datetime.now().date()
    print(date)
    print(os.getcwd()+"\..")
    # db = MongoDatabase()
