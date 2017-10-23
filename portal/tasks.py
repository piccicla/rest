# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         tasks.py
# Purpose:      celery tasks called by TaskSync and TaskAsync (in views.py)
#               these taskes will use the pysdss library
#
# Author:      claudio piccinini
#
# Updated:     04/10/2017
#-------------------------------------------------------------------------------

from celery import shared_task

from pysdss.geoprocessing import database as db

'''#########EXAMPLES##########
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
########################'''


@shared_task
def upload(*args, **kw):  # the result must be a  list

    #print(kw)
    return db.upload_metadata(*args, **kw)
    #print("ciao")
    #return [{"name":"", "type":"string", "kwargs":kw['METADATA_ID_TYPES']}] #test kw are there

@shared_task
def getfields(*args, **kw):

    #print(kw)
    return db.get_fields(*args, **kw)

@shared_task
def todatabase(*args, **kw):

    #print(kw)
    return db.upload_data(*args, **kw)

@shared_task
def getjson(*args, **kw):

    #print(kw)
    return db.get_json(*args, **kw)

@shared_task
def getvmap(*args, **kw):

    #print(kw)
    return db.get_vmap(*args, **kw)

@shared_task
def uploadids(*args, **kw):

    #print(kw)
    return db.upload_ids(*args, **kw)

@shared_task
def gettools(*args, **kw):

    #print(kw)
    return db.get_tools(*args, **kw)

@shared_task
def getdatasets(*args, **kw):

    #print(kw)
    return db.get_datasets(*args, **kw)

@shared_task
def getdatasetinfo(*args, **kw):

    #print(kw)
    return db.get_dataset_info(*args, **kw)

@shared_task
def addtool(*args, **kw):

    #print(kw)
    return db.add_tool(*args, **kw)



