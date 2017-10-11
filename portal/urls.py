from django.conf.urls import url
from portal import views

from portal import views_token
from portal import views_upload

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


    #####execute asynchronous geoprocessing task
    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/executeasync/$', views.TaskAsync.as_view(),name='execute-async'),

    #####asynchronous geoprocessing job status
    #url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>\w+)/$', views.JobDetail.as_view(), name='job-detail' ),# this will return the details of a job


    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})/$',
            views.JobDetail.as_view(), name='job-detail' ),

    ####cancel asynchronous geoprocessing job
    #url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>\w+)/cancel/$', views.JobCancel.as_view(), name='job-cancel') #this will cancel an asynchronous job

    url(r'^processing/(?P<service_name>\w+)/(?P<task_name>\w+)/jobs/(?P<job_id>[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12})/cancel/$', views.JobCancel.as_view(), name='job-cancel'),

    #login to get token, logout to delete token
    url(r'^login', views_token.login, name="login"),
    url(r'^logout', views_token.logout, name="logout"),


    #testing services
    #todo set the synch/asynch services
    #upload files
    url(r'^upload', views_upload.FileUploadView.as_view(), name="upload"),
    #get fields of uploaded file, user should pass the folder id and the filetype
    url(r'^getfields', views_upload.FileGetFieldsView.as_view(), name="getfields"),
    url(r'^todatabase', views_upload.DataUploadView.as_view(), name="upload_database"),
    url(r'^getjson', views_upload.DataGetGeoJSONView.as_view(), name="get_geojson")
    #,url(r'^getvmap', views_upload.DataGetVMapView.as_view(), name="get_vmap")

]
