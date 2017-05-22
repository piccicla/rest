##### testing functions in django rest framework
import numpy as np


class CalcClass():

    def __init__(self,*args, **kw):
        # Initialize any variables you need from the input you get
        pass
        self.arg1 = args[0]
        self.arg2 = args[1]

    def do_work(self):
        # Do some calculations here
        # returns a tuple ((1,2,3, ), (4,5,6,))

        if self.arg1 or self.arg2:  result=5
        else: result = ((1,2,3, ), (4,5,6,)) # final result
        return result

