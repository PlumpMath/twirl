#

class Deferred(object):
     def __init__(self):
         self.callbacks = []

     def errback(self, fail=None):
         for callback in self.callbacks:
             pass

     def callback(self, result):
         for cb, args, kwargs in self.callbacks:
             nArgs = []
             nArgs.append(result)
             nArgs = nArgs + args
             #
             cb(*nArgs, **kwargs)

     def addCallback(self, cb, args=None, kwargs=None):
         if args is None:
             args = []
         if kwargs is None:
             kwargs = {}
         self.callbacks.append((cb, args, kwargs))
