import io
import contextlib
import sys

class Maskable(object):
    def __init__(self,s):
        self.original_string = s
        self.printed_string = s      
 
    def __enter__(self):
        return self
        
    def test(self):
        print ("hello")

    def __exit__(self,  tp, value, traceback):
        pass

def hi():
    def test(func):
        func()

    def printout():
        print ("here!")

    q = '''def action():
            printout()

test(action)
            '''
    d = dict(locals(), **globals())
    exec(q, d, d)


hi()