# http://www.bogotobogo.com/python/python_differences_between_static_method_and_class_method_instance_method.php
# a.py
class A:
   message = "class message"

   @classmethod
   def cfoo(cls):
      print(cls.message)

   def foo(self, msg):
      self.message = msg
      print(self.message)

   def __str__(self):
      return self.message

# Because the method foo() is designed to process instances, we normally call the method through instance:
a = A()
a.foo('instance call')
# When we call the method, the Python automatically replace the self with 
# the instance object, a, and then the msg gets the string passed at the call which is 'instance call'.

# Methods may be called in two ways:
#  the first one through an instance which we did above. 
#  Another way of calling is by going through the class name as shown below:
# A.foo('class call')
# --->TypeError: unbound method foo() must be called with A instance as first argument (got str instance instead)
# We got the error because Python needs information about the instance.
#  We did not provide anything about the instance. 

#  So, we should use the following form when we call a method through a class name as the error message suggested:
A.foo(a, 'class call')
# Calls made through the instance and the class have the exact same effect,
#  as long as we pass the same instance object ourselves in the class form.

# For a class method, we can just simply call it through class name A:
A.cfoo()


# Note:
# Bound method (instance call): To call the method we must provide an instance object explicitly as the first argument.
#  (Python < 3.x). In python > 3.0, unbound method can be called through the class name.
# Unbound method (class call): Python automatically packages the instance with the function in the bound method object,
#  so we do not need pass an instance to call the method.

# STATIC METHOD
# I'll use function decorator(@) for static method, and the syntax looks like this:
# class S:
#    @staticmethod
#    def foo():
#       ...

# Internally, the definition has the same effect as the name rebinding:
# class S:
#    def foo():
#       ...
#    foo = staticmethod(foo)

# Suppose we have a typical instance counting code like this:
# s.py
class S:
   nInstances = 0
   def __init__(self):
      S.nInstances = S.nInstances + 1

   @staticmethod
   def howManyInstances():
      print('Number of instances created: ', S.nInstances)
a = S ()
b = S ()
c = S ()

# Now that we have static method, we can call it in two ways:

# call from class
# call from instances


S.howManyInstances()
a.howManyInstances()
