from abc import ABC, abstractmethod

class Base(ABC):

    @abstractmethod
    def pre_run(self, arg1):
        pass

    @abstractmethod
    def post_run(self, arg1):
        pass
