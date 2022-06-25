
import re
from abc import ABC, abstractmethod
# def on_bar(bar: MongodbBar):
#     print(bar.to_df())

class Test(ABC):
    @abstractmethod
    def foo(self):
        pass

class Beta(Test):
    def foo3(self, n):
        print(n)

if __name__ == "__main__":
    # engine = MainEngine()
    # bar_engine: BarEngine = engine.add_engine(BarEngine)
    # bar_engine.init(1, on_bar)

    # engine.connect()

    # contracts = engine.get_all_contracts()
    # a = "rB2210.SHFE"

    # print(re.match("\D*", a).group())

    b = Beta()
    
    
