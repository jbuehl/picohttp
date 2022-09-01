# Limited HTTP server for REST services

import socket
import sys
import mimetypes
import http.client
from rutifu import *
from .staticResource import *

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

class HttpServer(object):
    def __init__(self, port=80, handler=staticResource, args=(), threads=True, block=True, start=True):
        self.port = port
        self.handler = handler
        self.args = args
        self.threads = threads
        self.block = block
        self.socket = None
        if start:
            self.start()

    def start(self):
        debug("debugHttpServer", "httpserver", "starting")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", self.port))
        debug("debugHttpServer", "opened socket on port", self.port)
        self.socket.listen(1)
        startThread("httpserver", self.getRequests)
        if self.block:
            block()

    # wait for requests
    def getRequests(self):
        debug("debugHttpServer", "waiting for request")
        while True:
            (client, addr) = self.socket.accept()
            if self.threads:
                startThread("httpserver_"+str(addr[0])+"_"+str(addr[1]), self.handleConnection, args=(client, addr,))
            else:
                self.handleConnection(client, addr)

    def handleConnection(self, client, addr):
        request = HttpRequest()
        self.parseRequest(client, request)
        self.debugRequest(addr, request)
        # send it to the request handler
        response = HttpResponse("HTTP/1.0", 200, {}, None)
        try:
            self.handler(request, response, *self.args)
        except Exception as ex:
            logException("exception in request handler", ex)
            response.status = 500
            response.data = str(ex)+"\n"
        self.sendResponse(client, response)
        self.debugResponse(addr, response)
        client.close()

    def parseRequest(self, client, request):
        clientFile = client.makefile()
        # start a new request
        (request.method, uri, request.protocol) = fixedList(clientFile.readline().strip("\n").split(" "), 3, "")
        # parse the path string into components
        try:
            (pathStr, queryStr) = uri.split("?")
            request.query = dict([queryItem.split("=") for queryItem in queryStr.split("&")])
        except ValueError:
            pathStr = uri
            request.query = {}
        request.path = pathStr.lstrip("/").rstrip("/").split("/")
        # read the headers
        request.headers = {}
        (headerName, headerValue) = fixedList(clientFile.readline().strip("\n").split(":"), 2, "")
        while headerName != "":
            request.headers[headerName.strip()] = headerValue.strip()
            (headerName, headerValue) = fixedList(clientFile.readline().strip("\n").split(":"), 2, "")
        # read the data
        try:
            request.data = clientFile.read(int(request.headers["Content-Length"]))
        except KeyError:
            request.data = None
        clientFile.close()

    def sendResponse(self, client, response):
        if response.data:
            response.headers["Content-Length"] = len(response.data)
        else:
            response.headers["Content-Length"] = 0
        response.headers["Connection"] = "close"
        try:
            reason = http.client.responses[response.status]
        except KeyError:
            reason = ""
        client.send(bytes(response.protocol+" "+str(response.status)+" "+reason+"\n", "utf-8"))
        for header in response.headers:
            client.send(bytes(header+": "+str(response.headers[header])+"\n", "utf-8"))
        client.send(bytes("\n", "utf-8"))
        if response.data:
            if isinstance(response.data, str):
                client.send(bytes(response.data, "utf-8"))
            else:
                client.send(response.data)

    def debugRequest(self, addr, request):
        debug("debugHttpServer", "request from", addr)
        debug("debugHttpServer", "  method:", request.method, "protocol:", request.protocol)
        debug("debugHttpServer", "  path:", request.path, "query:", request.query)
        debug("debugHttpServer", "  headers:")
        for (header, value) in request.headers.items():
            debug("debugHttpServer", "    ", header+":", value)

    def debugResponse(self, addr, response):
        debug("debugHttpServer", "response to", addr)
        debug("debugHttpServer", "  protocol:", response.protocol, "status:", response.status)
        debug("debugHttpServer", "  headers:")
        for (header, value) in response.headers.items():
            debug("debugHttpServer", "    ", header+":", value)
