# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        views_token.py
# Purpose:
#
#
# Author:      claudio piccinini
#
# Updated:     14/08/2017
#-------------------------------------------------------------------------------

#   request.data -> contains the POST parameters
#   request.query_params -> contains the GET parameters
#   **kw -> contains part of the url as defined in urls.py


from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated

@api_view(["POST"])
@permission_classes((AllowAny, )) #allow everyone to access this view
def login(request):
    """
    Login to the application
    """
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "Login failed"}, status=HTTP_401_UNAUTHORIZED)
    #I store the username , this will be used to access the user folder in shared folders   "user/UID"
    request.session['username'] = username
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key})

@api_view(["POST"])
@permission_classes((IsAuthenticated, ))
def logout(request):
    """
    Logout from the application
    """
    # simply delete the token to force a login
    request.user.auth_token.delete()
    return Response(status=status.HTTP_200_OK)