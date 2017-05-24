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
from rest.celery import app

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

        tasks = [x['task'] for x in parsed_json['service'] if x['name'] == kw['service_name']]

        if tasks:
            s =  [s['name'] for s in tasks[0]]
            return Response({"success": True, "content": s} )
        else:
            return Response({"success": False,
                             "content": "service " + kw['service_name'] + " is not available"})

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

        #s = [x for x in [x['task'] for x in parsed_json['service'] if x['name'] == name][0] if x['name'] == tname]

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

        return Response({"success": True, "content": s})

'''
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


        ##todo: check all parameters are given correctly (compare with json file)

        ##Import the module with the task and use celery to start a synchronous process, wait for the response
        mod= importlib.import_module(s[0]['location'])  #this imports portal.tasks
        #t = mod.add.delay(4, 4)
        #use wait to wit for the result

        try:
            final_res = eval("mod."+s[0]['name']+".apply_async().wait(timeout=None, propagate=True, interval=0.5)")
            return Response({"success": True, "content": final_res})
        except Exception as e:
            return Response({"success": False, "content": eval(str(e))})

        #if final_res[0] == "error":
            #return Response(
                #{"success": False, "content": final_res})
        #else:
            #return Response(
                #{"success": True, "content":final_res})
'''

##################################

#TODO: adapt for post request
def check_params(s, request):

    """
    Check the required parameters are available
    :param s: the json fragment with the input parameters
    e.g:
        {
          "name":"synch",
          "info":"task for testing synchronous processing",
          "location":"portal.tasks",
          "type":"sync",
          "input":[
            {"name":"datasetid", "info":"the dataset id","type":"number", "required":true, "default":"","choicelist":[]}
          ],
          "output":[]
        },
    :param request: the django request . note that the request parameters are case sensitive
    :return: 
    parameters: a dictionary "parameter name": "value" 
    missing: a list of dictionaries, each dictionary is "parameter name": "parameter should be a number"  or
    "parameter name": "parameter is missing"
    """

    parameters = {}
    missing = []
    for input in s[0]['input']:  # check all the parameters are passed with the request
        # check the parameter name
        param = request.query_params.get(input["name"], None)
        # the parameter is there
        if param:
            # check the type (string or number)
            if input["type"] == "number":
                try:
                    parameters[input["name"]] = float(param)
                except:
                    missing.append({input["name"]: "parameter should be a number"})
            else:
                parameters[input["name"]] = param

        # if the prameter is not there check if not required and there is a default value
        elif not input['required']:
            if input['default']:  # if the parameter is not required there should be a default value
                parameters[input["name"]] = input['default']
            else:
                missing.append({input["name"]: "parameter is missing"})
        # param is not there and it is required
        else:
            missing.append({input["name"]: "parameter is missing"})

    return parameters, missing



class TaskSync(APIView):    ##########testing rest parameters
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

        #checking the required parameters are available
        #parameters is a dictionary "parameter name": "value"
        #missing is a list of dictionaries, each dictionary is "parameter name": "parameter should be a number"  or
        #"parameter name": "parameter is missing"

        parameters, missing = check_params(s, request)

        if missing:  #if some parameters are missing or the type is wrong (number instead of string)
            return Response({"success": False, "content": missing})

        #all the necessary parameters are available, therefore we can
        #import the module with the task and use celery to start a synchronous process, and wait for the response
        mod= importlib.import_module(s[0]['location'])  #this imports portal.tasks
        #t = mod.add.delay(4, 4)
        #use wait to wit for the result

        try:

            if parameters:
                #final_res = eval("mod."+s[0]['name']+".apply_async( kwargs=parameters).wait(timeout=None, propagate=True, interval=0.5)")
                #asyncresult =eval("mod."+s[0]['name']+".apply_async( kwargs=parameters)")
                final_res = eval("mod."+s[0]['name']+".apply_async( kwargs=parameters).wait(timeout=None, propagate=True, interval=0.5)")
            else: #no parameters are necessary
                final_res = eval("mod."+s[0]['name']+".apply_async().wait(timeout=None, propagate=True, interval=0.5)")

            return Response({"success": True, "content": final_res})
        except Exception as e:
            return Response({"success": False, "content": eval(str(e))})

        '''if final_res[0] == "error":
            return Response(
                {"success": False, "content": final_res})'''
        '''else:
            return Response(
                {"success": True, "content":final_res})'''


###################################


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
        if s[0]['type']=='sync':
            return Response({"success": False, "content": "task "+kw['service_name']+"/"+kw['task_name']+ " is synchronous!"})

        #t = add.delay(4, 4)


        ##todo: check all parameters are given correctly (compare with json file)

        ##Import the module with the task and use celery to start an asynchronous process, return the process id to the caller
        mod= importlib.import_module(s[0]['location'])  #this imports portal.tasks
        #t = mod.add.delay(4, 4)
        asyncresult= eval("mod."+s[0]['name']+".delay()")
        return Response({"success": True, "content": "starting asynchronous task "+kw['service_name']+"/"+kw['task_name'],"id": asyncresult.id})


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
                s = {"jobId": id, "jobStatus": state.lower(), "content":[]}
            elif state.lower() == "revoked":
                s = {"jobId": id, "jobStatus": "revoked", "content":[]}
            elif state.lower() == "retry":
                s = {"jobId": id, "jobStatus": "retry", "content": result.get()}
            elif state.lower() == "failure":
                s = {"jobId": id, "jobStatus": "failure", "content": result.get()}
            elif state.lower() == "success":
                s = {"jobId": id, "jobStatus": "success", "content": result.get()}
            else:
                s = {"jobId": id, "jobStatus": "unknown", "content": result.get()}
            return Response(s)

        except Exception as e: #this will intercept the error raised by pysdss in the form ["error","error info here"]
            s = {"jobId": id, "jobStatus": 'failure', "content":eval(str(e))}
            return Response(s)


#TODO check the terminate parameter
class JobCancel(APIView):
    """
    Geoprocessing task: cancel
    When a worker receives a revoke request it will skip executing the task, but it won’t terminate an already executing task unless the terminate option is set.
    NOTE:The terminate option is a last resort for administrators when a task is stuck. It’s not for terminating the task, it’s for terminating the process that’s
     executing the task, and that process may have already started processing another task at the point when the signal is sent, so for this reason you must never call this programmatically.
    """
    def get(self, request, *args, **kw):
        name = kw['service_name']
        tname = kw['task_name']
        id= kw['job_id']

        app.control.revoke(id, terminate=True)

        s = {"jobId": id, "jobStatus": "revoked", "content":[]}
        return Response(s)

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