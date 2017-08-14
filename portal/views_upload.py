# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        views_upload.py
# Purpose:     manage upload files (.csv, shapefiles)
#
#
# Author:      claudio piccinini
#
# Updated:     14/08/2017
#-------------------------------------------------------------------------------

#   request.data -> contains the POST parameters
#   request.query_params -> contains the GET parameters
#   **kw -> contains part of the url as defined in urls.py


import os.path
import zipfile
import csv
import shapefile

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework.parsers import MultiPartParser, FormParser
####http://www.django-rest-framework.org/api-guide/parsers/
####FORMPARSER
#Parses HTML form content. request.data will be populated with a QueryDict of data.
#You will typically want to use both FormParser and MultiPartParser together in order to fully support HTML form data.
#.media_type: application/x-www-form-urlencoded
####MULTIPARTPARSER
#Parses multipart HTML form content, which supports file uploads. Both request.data will be populated with a QueryDict.
#You will typically want to use both FormParser and MultiPartParser together in order to fully support HTML form data.
#.media_type: multipart/form-data


## use a POST or PUT request
#curl -X POST -H 'Content-Type:multipart/form-data' -F 'data=@/{your_file}' -u {account}:{password} http://{your server ip address}
## tests
#1OK
#curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/2016_06_17.csv' http://localhost:8000/upload
#2wrong format
#curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/2016_06_17.txt' http://localhost:8000/upload
#3OK
#curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/shape.zip' http://localhost:8000/upload
#4 wrong zip content
#curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/badshape.zip' http://localhost:8000/upload


from pysdss import utils

#todo: check upload max size
class FileUploadView(APIView):
    """
    Upload file to the application. Allowed files are .csv text files and .zip  files (use .zip to upload shapefiles). csv first row must have field names!
    """

    parser_classes = (MultiPartParser,FormParser, )
    #permission_classes = (IsAuthenticated,)  # only authenticad users can upload files

    #todo: create custom authentication response  like {"success": False, "content": "user is not authenticated; use login and try again"}
    #if authentication fails we get {"detail": "Authentication credentials were not provided."}
    ###for custom error see:
    #https://stackoverflow.com/questions/33217441/custom-response-for-invalid-token-authentication-in-django-rest-framework
    #https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py
    #https://github.com/encode/django-rest-framework/blob/3eade5abeb77726a7ac3cbd333672a80bf766d01/rest_framework/exceptions.py

    def post(self, request, format=None):

        try:

            up_file = request.FILES['file']
            # create unique identifier to name the folder
            idf = utils.create_uniqueid()

            #check extension, if not correct
            if up_file.name.split('.')[-1] not in settings.UPLOAD_FORMATS:
                return Response({"success": False, "content": "format should be one of " + str(settings.UPLOAD_FORMATS)})

            if not os.path.exists(settings.UPLOAD_ROOT + idf): os.mkdir(settings.UPLOAD_ROOT + idf)

            destination = open(settings.UPLOAD_ROOT + idf + "/" + up_file.name, 'wb')
            for chunk in up_file.chunks():
                destination.write(chunk)
                destination.close()

            # check .zip has a shapefile and unzip it if OK
            if up_file.name.split('.')[-1].lower() == "zip":
                zipShape=None
                z=None
                try:
                    z = open(settings.UPLOAD_ROOT + idf + "/" + up_file.name, "rb")
                    zipShape = zipfile.ZipFile(z)
                    # extract file suffixes in a set
                    zfiles = { i.split('.')[-1] for i in zipShape.namelist()}
                    #and check the mandatory shapefile files are there
                    if not zfiles>=set(settings.SHAPE_MANDATORY_FILES):
                        return Response({"success": False, "content": "shapefiles files should be " + str(settings.SHAPE_MANDATORY_FILES)})
                    else:
                        for fileName in zipShape.namelist():  # unzip files
                            out = open(settings.UPLOAD_ROOT + idf + "/" + fileName, "wb")
                            out.write(zipShape.read(fileName))
                            out.close()
                except Exception as e:
                    return Response({"success": False, "content": "problems extracting the zip file, try to upload again"})
                finally:
                    if zipShape: zipShape.close()
                    if z: z.close()

            # ...
            # do some stuff with uploaded file
            #    file = request.Files['data']
            #   data = file.read(
            # ...

            #return Response(up_file.name, status.HTTP_201_CREATED)
            return Response({"success": True, "content": [idf,up_file.name.split('.')[-1]]})
        except Exception as e:
            return Response({"success": False, "content": str(e)})



#todo: check upload max size
class FileGetFieldsView(APIView):
    """
    Get the fields for the uploaded file
    require folderID and filetype(csv or shapefile)
    """

    '''
    Value | Shape Type
    0  | Null Shape
    1  | Point
    3  | PolyLine
    5  | Polygon
    8  | MultiPoint
    11 | PointZ
    13 | PolyLineZ
    15 | PolygonZ
    18 | MultiPointZ
    21 | PointM
    23 | PolyLineM
    25 | PolygonM
    28 | MultiPointM
    31 | MultiPatch
    '''

    parser_classes = (MultiPartParser,FormParser, )
    #permission_classes = (IsAuthenticated,)  # only authenticad users can upload files

    def post(self, request,  *args, **kw):
        try:
            idf = request.data.get('id')
            ftype = request.data.get('filetype')
            if (idf and ftype):
                if (not os.path.exists(settings.UPLOAD_ROOT + idf) or  ftype not in settings.UPLOAD_FORMATS):
                    raise Exception("check id and file type")

                if ftype == "csv":
                    fields=["not_available"]
                    #open csv and read first line
                    files = os.listdir(settings.UPLOAD_ROOT + idf)
                    file = [i for i in files if i.endswith("csv")]

                    if not file: return Response({"success": False, "content": "a csv file was not found, check the request"})

                    f = open(settings.UPLOAD_ROOT + idf + "/" +file[0])
                    reader = csv.reader(f)
                    fields += reader.__next__() #read just the first row
                    f.close()

                    return Response({"success": True, "content": fields})

                elif ftype == "zip":
                    fields = ["not_available"]
                    # open shape
                    # read fields
                    files = os.listdir(settings.UPLOAD_ROOT + idf)
                    file = [i.split(".")[0] for i in files if i.endswith("shp")]

                    if not file: return Response({"success": False, "content": "a shpefile was not found, check the request"})

                    #check this is a point
                    sf = shapefile.Reader(settings.UPLOAD_ROOT + idf +"/"+file[0])
                    shapes = sf.shapes()
                    if shapes[0].shapeType not in [1,8,18,28]:  #shapetypes, see above list
                        return Response({"success": False, "content": "a point shapefile is required, upload a new file"})

                    return Response({"success": True, "content": fields+[field[0] for field in sf.fields]})

            else:
                return Response({"success": False, "content": "request should contain 'id' and 'filetype'"})

        except Exception as e:
            return Response({"success": False, "content": str(e)})
