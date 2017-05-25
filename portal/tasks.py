from celery import shared_task

from pysdss.geoprocessing import hellocelery as hello


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def synch(*args, **kw):  # the result must be a  list
    return hello.synchronous_test_1(*args, **kw)
    #print("ciao")
    #return [{"name":"", "type":"string", "kwargs":[kw]}] #test kw are there

@shared_task
def asynch(*args, **kw): # the result must be a  list
    return hello.asynchronous_test_1(*args, **kw)