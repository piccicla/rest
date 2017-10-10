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
#curl -X POST -H 'Content-Type:multipart/form-data' -F 'data=@/{your_file}'  -F 'parameter=value' -F 'parameter=value' -u {account}:{password} http://{your server ip address}


from pysdss import utils
from pysdss.database import query

#todo: check upload max size
class FileUploadView(APIView):
    """
    Upload file to the application. Allowed files are .csv text files and .zip  files (use .zip to upload shapefiles). csv first row must have field names!
    metadata fields need to be passed. Also "metatable" (yield,soil,canopy,sensor) and "toolid" (id from xxxtype tables) are necessary
    """

    ## tests
    # 1 parameters missing
    # curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/2016_06_17.csv' http://localhost:8000/upload
    # 2wrong format
    # curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/2016_06_17.txt' -F 'metatable=sensor' -F 'toolid=1' -F 'datetime=2017-08-15%2014:19:25.63' -F 'roworientation=NE' http://localhost:8000/upload
    # 3OK
    # curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/shape.zip'  -F 'metatable=sensor' -F 'toolid=1' -F 'datetime=2017-08-15%2014:19:25.63' -F 'roworientation=NE' http://localhost:8000/upload
    # 4 wrong zip content
    # curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/badshape.zip' -F 'metatable=sensor' -F 'toolid=1' -F 'datetime=2017-08-15%2014:19:25.63' -F 'roworientation=NE' http://localhost:8000/upload
    # 5 OK
    # curl -X POST -H 'Content-Type:multipart/form-data' -F 'file=@//vagrant/code/pysdss/data/input/2016_06_17.csv' -F 'metatable=sensor' -F 'toolid=1' -F 'datetime=2017-08-15%2014:19:25.63' -F 'roworientation=NE' http://localhost:8000/upload


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
            if not up_file:
                #raise Exception("file is missing, upload again")
                return Response({"success": False, "content": "file is missing, upload again"})

            #check mandatory metadata fields   #todo: should this be done with the geoprocessing.json file?
            for i in settings.METADATA_MANDATORY_FIELDS:
                if not request.data.get(i):
                    #raise Exception("mandatory POST parameter " + i + " must be available")
                    return Response({"success": False, "content": "mandatory POST parameter " + i + " must be available"})

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
                except Exception as e: #for any other unexpected error
                    return Response({"success": False, "content": "problems extracting the zip file, try to upload again"})
                finally:
                    if zipShape: zipShape.close()
                    if z: z.close()

            # ...
            # do some stuff with uploaded file
            #    file = request.Files['data']
            #   data = file.read(
            # ...

            #upload the metadata to the database table and get back the id for the new row

            # todo: this is to be converted to a celery process, but it is necessary to delete the inmemory file from the request data to avoid serialization errors

            iddataset = query.upload_metadata(request.data, settings.METADATA_ID_TYPES, settings.METADATA_FIELDS_TYPES,
                                              settings.METADATA_IDS)


            #return Response(up_file.name, status.HTTP_201_CREATED)

            #return the folderID, the metadata newrow ID, and the file extension
            return Response({"success": True, "content": [idf,iddataset, up_file.name.split('.')[-1]]})
        except Exception as e:
            return Response({"success": False, "content": str(e)}) #errors coming from query.upload_metadata


class DataUploadView(APIView):
    """
    Upload the actual data to the database. Post parameters include the "metatable" (yield,soil,canopy,sensor), the "datasetid" of
    the dataset (from the "metatable"), the mapping for "lat", "lon", "value1", the optional mapping for "row"  and the additional value2,3,4,5,6,  the
    "folderID", the "filename" (note, for shpefile the suffix is .zip)

    "not_available" is not allowed for the value1
    """

    #########tests
    #csv with 'row'
    #curl -X  POST -H  'Content-Type:multipart/form-data' -F 'metatable=canopy' -F 'filename=2017-07-25 To Kalon NDVI.csv' -F 'folderid=a5f9e0915ecb94449b26a8dc52b970cc0' -F 'datasetid=1' -F 'lat=lat' -F 'lon=lng' -F 'value1=sf01' -F 'row=sensor_addr' http://localhost:8000/processing/todatabase
    #csv without 'row'
    #curl -X  POST -H  'Content-Type:multipart/form-data' -F 'metatable=canopy' -F 'filename=2017-07-25 To Kalon NDVI.csv' -F 'folderid=a5f9e0915ecb94449b26a8dc52b970cc0' -F 'datasetid=1' -F 'lat=lat' -F 'lon=lng' -F 'value1=sf01' http://localhost:8000/todatabase
    #shapefile with 'row'
    #curl -X  POST -H  'Content-Type:multipart/form-data' -F 'metatable=canopy' -F 'filename=ToKalonNDVI.zip' -F 'folderid=a5f9e0915ecb94449b26a8dc52b970cc0' -F 'datasetid=1' -F 'lat=lat' -F 'lon=lng' -F 'value1=sf01' -F 'row=sensor_add' http://localhost:8000/todatabase
    #shapefile without 'row'
    #curl -X  POST -H  'Content-Type:multipart/form-data' -F 'metatable=canopy' -F 'filename=ToKalonNDVI.zip' -F 'folderid=a5f9e0915ecb94449b26a8dc52b970cc0' -F 'datasetid=1' -F 'lat=lat' -F 'lon=lng' -F 'value1=sf01' http://localhost:8000/todatabase


    parser_classes = (MultiPartParser,FormParser, )
    #permission_classes = (IsAuthenticated,)  # only authenticad users can upload files

    def post(self, request, format=None):
        try:

            #check parameters
            metatable = request.data.get('metatable')
            idd = request.data.get('datasetid')
            lat = request.data.get('lat')
            lon = request.data.get('lon')
            value = request.data.get('value1')
            folderid = request.data.get('folderid')
            filename = request.data.get('filename')

            if not all([metatable, idd, lat, lon, value, folderid, filename]):
                #raise Exception("some POST parameters are missing")
                return Response({"success": False,"content": "some POST parameters are missing"})

            if value == "not_available":
                return Response({"success": False,"content": "value1 cannot be set to 'not_available'"})
            if filename.lower().split('.')[-1] not in settings.UPLOAD_FORMATS:
                #raise Exception("format should be one of " + str(settings.UPLOAD_FORMATS))
                return Response({"success": False, "content": "format should be one of " + str(settings.UPLOAD_FORMATS)})
            #open the file


            #upload to database
            #
            query.upload_data(request.data,settings.METADATA_DATA_TABLES,settings.METADATA_IDS, settings.UPLOAD_ROOT)
            #automatically get the WGS84 UTM zone

            #insert geometry

            #commit
            #conn.commit()


            return Response({"success": True, "content": "data uploaded"})
        except Exception as e:
            return Response({"success": False, "content": str(e)})

#todo: check upload max size
class FileGetFieldsView(APIView):
    """
    Get the fields for the uploaded file
    require folderid and filetype csv or zip(shapefile)
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
            idf = request.data.get('folderid')
            ftype = request.data.get('fileformat')
            if (idf and ftype):
                if (not os.path.exists(settings.UPLOAD_ROOT + idf) or  ftype not in settings.UPLOAD_FORMATS):
                    raise Exception("request should contain a correct 'folderid' and 'fileformat'")

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
                    if shapes[0].shapeType not in [1,11,21]:  #check point shapetypes, no multypoint
                        return Response({"success": False, "content": "a point shapefile is required, upload a new file"})

                    return Response({"success": True, "content": fields+[field[0].strip().lower() for field in sf.fields]})

            else:
                return Response({"success": False, "content": "request should contain a correct 'folderid' and 'filetype'"})

        except Exception as e:
            return Response({"success": False, "content": str(e)})



class DataGetGeoJSONView(APIView):
    """
    Get geojson for a dataset

    """
    #curl -X  POST -H  'Content-Type:multipart/form-data' -F 'metatable=canopy'  -F 'iddataset=1'  http://localhost:8000/processing/getjson

    parser_classes = (MultiPartParser,FormParser, )
    #permission_classes = (IsAuthenticated,)  # only authenticad users can upload files


    def post(self, request, format=None):
        try:


            #check parameters
            metatable = request.data.get('metatable')
            idd = request.data.get('iddataset')

            #todo check parameters
            result = query.get_geojson(request.data,settings.METADATA_DATA_TABLES, settings.METADATA_IDS, settings.DATA_IDS, limit=100000)

            return Response({"success": True, "content": result})

        except Exception as e:
            return Response({"success": False, "content": str(e)})
