# Static resource server

import sys
import mimetypes
from rutifu import *

def staticResource(request, response, staticBase="",
                    defaultResource="index.html", defaultMime="text/plain"):
    if request.method == "GET":
        filePath = staticBase+"/".join(request.path)
        if request.path[0] == "":
            filePath += defaultResource
        try:
            with open(filePath, "rb") as resourceFile:
                response.data = resourceFile.read()
                mimeType = mimetypes.guess_type(filePath)[0]
                if not mimeType:
                    mimeType = defaultMime
                response.headers['Content-Type'] = mimeType
        except FileNotFoundError:
            response.status = 404
    else:
        response.status = 501
