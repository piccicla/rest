from django.conf.urls import url
from portal import views

urlpatterns = [

    ####tests#####
    url(r'^geoprocessing/$', views.MyRESTView.as_view()),
    url(r'^geoprocessing/(?P<resource_id>\d+)[/]?$', views.MyRESTView.as_view()),  #this will add resource_id to the kwargs
    #############


    ####root
    url(r'^processing/$', views.APIRootView.as_view(), name='api-root'),

    ####geoprocessing service
    url(r'^processing/services/$', views.GeoservicesList.as_view(), name='geoservices-list'), #this will return a list of available services
    url(r'^processing/(?P<service_name>\w+)/$', views.GeoservicesDetail.as_view(), name='geoservice-detail'), # this will return the details of a service

    #####geoprocessing task
    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/$', views.TaskDetail.as_view(), name='task-detail'),# this will return the details of a task

    #####execute synchronous geoprocessing task
    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/executesync/$', views.TaskSync.as_view(), name='execute-sync'),
    # this will return the details of a task

    #####execute asynchronous geoprocessing task
    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/executeasync/$', views.TaskAsync.as_view(),name='execute-async'),

    #####asynchronous geoprocessing job status
    #url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>\w+)/$', views.JobDetail.as_view(), name='job-detail' ),# this will return the details of a job


    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})/$',
            views.JobDetail.as_view(), name='job-detail' ),

    ####cancel asynchronous geoprocessing job
    #url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>\w+)/cancel/$', views.JobCancel.as_view(), name='job-cancel') #this will cancel an asynchronous job

    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})/cancel/$', views.JobCancel.as_view(), name='job-cancel')
]
