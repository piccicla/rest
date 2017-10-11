# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         checking.py
# Purpose:      code to perform checks on specific services
#
#
# Author:      claudio piccinini
#
# Updated:     03/10/2017
#-------------------------------------------------------------------------------



import urllib.parse as parse
import os.path
import zipfile
import csv
import shapefile

from rest_framework.response import Response

#import the settings
from django.conf import settings
CHECK_SERVICES =  settings.CHECK_SERVICES

from pysdss import utils


def check_services(request, k):
    """

    :param request: the django request . note that the request parameters are case sensitive
    :param k: the method name to be called
    :return: [True, <newparameters>] when no problem, otherwise [False,'<message>'] when something wrong
                {<newparameters>} is a dictionary with new parameters that will be passed to the celery task
    """

    # call the method
    r = eval(k + "(request)")
    return r


########checking methods#######
#  return [True, {<newparameters>}] when no problem, the dictionary with new parameters will be passed to the celery task
#  return [False,'<message>'] when something wrong

def check_file_upload(request):
    """
    Check the uploaded files are csv or zipped shapefiles
    :param request: the django request object with the request parameters
    :return: [True, {<newparameters>}] when no problem, otherwise [False,'<message>']
    """

    # create unique identifier to name the folder
    idf = utils.create_uniqueid()

    # check extension, if not correct
    up_file = request.FILES['file']
    if up_file.name.split('.')[-1] not in settings.UPLOAD_FORMATS:
        #return Response({"success": False, "content": "format should be one of " + str(settings.UPLOAD_FORMATS)})
        return [False,"format should be one of " + str(settings.UPLOAD_FORMATS)]

    if not os.path.exists(settings.UPLOAD_ROOT + idf): os.mkdir(settings.UPLOAD_ROOT + idf)

    destination = open(settings.UPLOAD_ROOT + idf + "/" + up_file.name, 'wb')
    for chunk in up_file.chunks():
        destination.write(chunk)
        destination.close()

    # check .zip has a shapefile and unzip it if OK
    if up_file.name.split('.')[-1].lower() == "zip":
        zipShape = None
        z = None
        try:
            z = open(settings.UPLOAD_ROOT + idf + "/" + up_file.name, "rb")
            zipShape = zipfile.ZipFile(z)
            # extract file suffixes in a set
            zfiles = {i.split('.')[-1] for i in zipShape.namelist()}
            # and check the mandatory shapefile files are there
            if not zfiles >= set(settings.SHAPE_MANDATORY_FILES):
                #return Response({"success": False, "content": "shapefiles files should be " + str(settings.SHAPE_MANDATORY_FILES)})
                return [False,"shapefiles files should be " + str(settings.SHAPE_MANDATORY_FILES)]
            else:
                for fileName in zipShape.namelist():  # unzip files
                    out = open(settings.UPLOAD_ROOT + idf + "/" + fileName, "wb")
                    out.write(zipShape.read(fileName))
                    out.close()
        except Exception as e:  # for any other unexpected error
            #return Response({"success": False, "content": "problems extracting the zip file, try to upload again"})
            return [False, "problems extracting the zip file, try to upload again"]
        finally:
            if zipShape: zipShape.close()
            if z: z.close()

    # if no problem returns the folder ID and the file extension plus settings necessary to upload files to database
    return [True, {'idf':idf, 'fl_ext':up_file.name.split('.')[-1], 'METADATA_ID_TYPES': settings.METADATA_ID_TYPES,
                   'METADATA_FIELDS_TYPES': settings.METADATA_FIELDS_TYPES,'METADATA_IDS':settings.METADATA_IDS}]


def check_getfields(request):
    """
    just return the UPLOAD_ROOT and UPLOAD_FORMATS
    :param request:
    :return:
    """
    # if no problem returns the folder ID and the file extension plus settings necessary to upload files to database
    return [True, {'UPLOAD_ROOT': settings.UPLOAD_ROOT,'UPLOAD_FORMATS': settings.UPLOAD_FORMATS}]


def check_data_upload(request):
    """
    Check the value1 and the format, add additional rarameters
    :param request: the django request object with the request parameters
    :return: [True, {<newparameters>}] when no problem, otherwise [False,'<message>']
    """

    value = parse.unquote(request.data.get('value1'))
    filename = parse.unquote(request.data.get('filename'))

    if value == "not_available":
        return [False,"value1 cannot be set to 'not_available'"]
    if filename.lower().split('.')[-1] not in settings.UPLOAD_FORMATS:
        # raise Exception("format should be one of " + str(settings.UPLOAD_FORMATS))
        return [False,"format should be one of " + str(settings.UPLOAD_FORMATS)]

    return [True, {"METADATA_DATA_TABLES" : settings.METADATA_DATA_TABLES,"METADATA_IDS" : settings.METADATA_IDS,
                   "UPLOAD_ROOT" :settings.UPLOAD_ROOT}]


def check_getjson(request):
    """
    just return the UPLOAD_ROOT and UPLOAD_FORMATS
    :param request:
    :return:
    """
    # if no problem returns the folder ID and the file extension plus settings necessary to upload files to database

    return [True, {'METADATA_DATA_TABLES':settings.METADATA_DATA_TABLES, 'METADATA_IDS':settings.METADATA_IDS,
                   'DATA_IDS':settings.DATA_IDS}]


def check_getvmap(request):
    """
    just return the UPLOAD_ROOT and UPLOAD_FORMATS
    :param request:
    :return:
    """
    # if no problem returns the folder ID and the file extension plus settings necessary to upload files to database

    return [True, {'METADATA_IDS':settings.METADATA_IDS}]


def check_uploadids(request):
    """
    just return the UPLOAD_ROOT and UPLOAD_FORMATS
    :param request:
    :return:
    """
    # if no problem returns the folder ID and the file extension plus settings necessary to upload files to database
    return [True, {'METADATA_DATA_TABLES':settings.METADATA_DATA_TABLES,'METADATA_IDS':settings.METADATA_IDS,'DATA_IDS':settings.DATA_IDS,"UPLOAD_ROOT" :settings.UPLOAD_ROOT}]