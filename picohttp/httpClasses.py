# common class definitions and functions

from rutifu import *

class HttpRequest(object):
    def __init__(self, method="", path=[], query={}, protocol="", headers={}, data=None):
        self.method = method
        self.path = path
        self.query = query
        self.protocol = protocol
        self.headers = headers
        self.data = data

class HttpResponse(object):
    def __init__(self, protocol, status=200, headers={}, data=None):
        self.protocol = protocol
        self.status = status
        self.headers = headers
        self.data = data

def debugRequest(debugVar, addr, request):
    type = debugVar[5:]
    debug(debugVar, type, "request", "from" if type == "HttpServer" else "to", addr)
    debug(debugVar, type, "  method:", request.method, "protocol:", request.protocol)
    debug(debugVar, type, "  path:", request.path, "query:", request.query)
    debug(debugVar, type, "  headers:")
    for (header, value) in request.headers.items():
        debug(debugVar, type, "    ", header+":", value)

def debugResponse(debugVar, addr, response):
    type = debugVar[5:]
    debug(debugVar, type, "response", "to" if type == "HttpServer" else "from", addr)
    debug(debugVar, type, "  protocol:", response.protocol, "status:", response.status)
    debug(debugVar, type, "  headers:")
    for (header, value) in response.headers.items():
        debug(debugVar, type, "    ", header+":", value)
