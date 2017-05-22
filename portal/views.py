from django.shortcuts import render

# Create your views here.
import json
import os

import time

import importlib



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.reverse import reverse

from celery.result import AsyncResult


import portal.processing as pr

PROCESSING_SETTINGS_URL = "/settings/geoprocessing.json"



class APIRootView(APIView):
    def get(self, request):
        data = {
            'geoservices-list-url': reverse('geoservices-list',   request=request),
            'geoservice-detail-url': reverse('geoservice-detail',args=['colorgrade'], request=request),
            'task-detail-url': reverse('task-detail',args=['colorgrade','berrycolor_workflow'],request=request),
            'execute-sync-url': reverse('execute-sync',args=['colorgrade','berrycolor_workflow'],request=request),
            'execute-async-url': reverse('execute-async',args=['colorgrade','berrycolor_workflow'],request=request),
            'job-detail-url': reverse('job-detail',args=['colorgrade','berrycolor_workflow','00000000-0000-0000-0000-000000000000'],request=request),
            'job-cancel-url': reverse('job-cancel',args=['colorgrade','berrycolor_workflow','00000000-0000-0000-0000-000000000000'],request=request)
        }
        return Response(data)



class GeoservicesList(APIView):
    """
    Geoprocessing services: a list of available services
    e.g. http://localhost:8100/processing/services/
    """
    def get(self, request, *args, **kw):

        f= open(os.path.dirname(__file__)+PROCESSING_SETTINGS_URL)
        parsed_json = json.load(f)
        s = sorted([s['name'] for s in parsed_json['service']])
        return Response({"success": True, "content": s} )


class GeoservicesDetail(APIView):
    """
    Geoprocessing services: the details of a service
    e.g http://localhost:8100/processing/colorgrade/
    """
    def get(self, request, *args, **kw):

        f= open(os.path.dirname(__file__)+PROCESSING_SETTINGS_URL)
        name = kw['service_name']
        parsed_json = json.load(f)
        s =  [s['name'] for s in [x['task'] for x in parsed_json['service'] if x['name'] == kw['service_name']][0]]
        return Response({"success": True, "content": s} )


class TaskDetail(APIView):
    """
    Geoprocessing task: the details of a task
        e.g http://localhost:8100/processing/colorgrade/berrycolor_workflow/
    """
    def get(self, request, *args, **kw):

        f= open(os.path.dirname(__file__)+PROCESSING_SETTINGS_URL)
        name = kw['service_name']
        tname = kw['task_name']
        parsed_json = json.load(f)
        s = [x for x in [x['task'] for x in parsed_json['service'] if x['name'] == name][0] if x['name'] == tname]

        return Response({"success": True, "content": s})


class TaskSync(APIView):
    """
    Start a synchronous task
    e.g. http://localhost:8100/processing/database/upload_berrycolor_data/executesync/
    """
    def get(self, request, *args, **kw):

        name = kw['service_name']
        tname = kw['task_name']

        f= open(os.path.dirname(__file__)+PROCESSING_SETTINGS_URL)
        parsed_json = json.load(f)

        # check the service exists
        serv = [x['task'] for x in parsed_json['service'] if x['name'] == name]
        if not serv: #serv
            return Response({"success": False,
                             "content": "service " + kw['service_name'] + " is not available"})

        # check the task exists
        s = [x for x in serv[0] if x['name'] == tname]
        if not s: #s==[]
            return Response({"success": False,
                             "content": "task " + kw['service_name'] + "/" + kw['task_name'] + " is not available"})

        if s[0]['type']=='async':
            return Response({"success": False, "content": "task "+kw['service_name']+"/"+kw['task_name']+ " is asynchronous"})


        ##todo: check all parameters are given

        ##todo: use celery to start a synchronous process and wait for the response

        mod= importlib.import_module(s[0]['location'])  #this imports portal.tasks
        #t = mod.add.delay(4, 4)
        #use wait to wit for the result
        final_res = eval("mod."+s[0]['name']+".apply_async().wait(timeout=None, propagate=True, interval=0.5)")

        return Response(
            {"success": True, "content":final_res})


class TaskAsync(APIView):
    """
    Start an asynchronous task
    
    """
    def get(self, request, *args, **kw):

        name = kw['service_name']
        tname = kw['task_name']

        f= open(os.path.dirname(__file__)+PROCESSING_SETTINGS_URL)
        parsed_json = json.load(f)

        # check the service exists
        serv = [x['task'] for x in parsed_json['service'] if x['name'] == name]
        if not serv: #serv
            return Response({"success": False,
                             "content": "service " + kw['service_name'] + " is not available"})
        # check the task exists
        s = [x for x in serv[0] if x['name'] == tname]
        if not s: #s==[]
            return Response({"success": False,
                             "content": "task " + kw['service_name'] + "/" + kw['task_name'] + " is not available"})
        if s=='sync':
            return Response({"success": False, "content": "task "+kw['service_name']+"/"+kw['task_name']+ " is synchronous!"})

        #t = add.delay(4, 4)

        mod= importlib.import_module(s[0]['location'])  #this imports portal.tasks
        #t = mod.add.delay(4, 4)
        t = eval("mod."+s[0]['name']+".delay()")
        ##todo: check all parameters are given
        return Response({"success": True, "content": {"message":"starting asynchronous task "+kw['service_name']+"/"+kw['task_name'],"id": t.id}})


class JobDetail(APIView):
    """
    Geoprocessing task: the details of a task
    """

    """
    
    Possible celery states 
    PENDING
    Task is waiting for execution or unknown. Any task id that’s not known is implied to be in the pending state.
    STARTED
    Task has been started. Not reported by default, to enable please see app.Task.track_started.
    meta-data:	pid and hostname of the worker process executing the task.
    SUCCESS
    Task has been successfully executed. 
    meta-data:	result contains the return value of the task.
    propagates:	Yes
    ready:	Yes
    FAILURE
    Task execution resulted in failure. 
    meta-data:	result contains the exception occurred, and traceback contains the backtrace of the stack at the point when the exception was raised.
    propagates:	Yes
    RETRY
    Task is being retried. 
    meta-data:	result contains the exception that caused the retry, and traceback contains the backtrace of the stack at the point when the exceptions was raised.
    propagates:	No
    REVOKED
    Task has been revoked.   
    propagates:	Yes
    """


    def get(self, request, *args, **kw):

        name = kw['service_name']
        tname = kw['task_name']
        id= kw['job_id']

        #f= open(os.path.dirname(__file__)+PROCESSING_SETTINGS_URL)
        #parsed_json = json.load(f)

        #query result backend for details
        try:

            result = AsyncResult(id=id)
            state = result.state

            if state.lower() in ["pending","started"] :
                s = {"jobId": id, "jobStatus": state.lower(), "result":{"value" : ""}}
            elif state.lower() == "revoked":
                s = {"jobId": id, "jobStatus": "revoked", "result":{"value": ""}}
            elif state.lower() == "retry":
                s = {"jobId": id, "jobStatus": "revoked", "result": {"value": result.get()}}
            elif state.lower() == "failure":
                s = {"jobId": id, "jobStatus": "failure", "result": {"value": result.get()}}
            elif state.lower() == "success":
                s = {"jobId": id, "jobStatus": "success", "result": {"value": result.get()}}
            else:
                s = {"jobId": id, "jobStatus": "unknown", "result": {"value": result.get()}}
            return Response(s)

        except Exception as e:
            s = {"jobId": id, "jobStatus": 'failure', "result":{"value":str(e)}}
            return Response(s)

class JobCancel(APIView):
    """
    Geoprocessing task: cancel
    """
    def get(self, request, *args, **kw):
        name = kw['service_name']
        tname = kw['task_name']
        id= kw['job_id']

        s = {"jobId": id, "jobStatus": "cancelled"}
        return Response({"success": True, "content": s})

######################TESTS################

from portal.processing import CalcClass
class MyRESTView(APIView):
    """
    Simple Geoprocessing 
    """
    def get(self, request, *args, **kw):
        # Process any get params that you may need
        # If you don't need to process get params,
        # you can skip this part
        get_arg1 = request.query_params.get('arg1', None) #get arg1 else set to None
        get_arg2 = request.query_params.get('arg2', None)

        # Any URL parameters get passed in **kw
        myClass = CalcClass(get_arg1, get_arg2, **kw)

        #myClass =  CalcClass()

        result = myClass.do_work()
        response = Response(result, status=status.HTTP_200_OK)
        return response

    def post(self, request, *args, **kw):
        #return Response({"success": True, "content": "Hello World!"})
        return Response(request.data)


class CustomGet(APIView):
  """
  A custom endpoint for GET request.
  """
  def get(self, request, format=None):
    """
    Return a hardcoded response.
    """
    return Response({"success": True, "content": "Hello World!"})
#####################################################