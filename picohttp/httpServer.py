# Limited HTTP server for REST services

import socket
import sys
import mimetypes
import http.client
import urllib.parse
from rutifu import *
from .httpClasses import *
from .staticResource import *

class HttpServer(object):
    def __init__(self, port=80, handler=staticResource, args=(), threads=True, reuse=True, block=True, start=True):
        self.ports = listize(port)
        self.port = 0
        self.handler = handler
        self.args = args
        self.threads = threads
        self.reuse = reuse
        self.block = block
        self.socket = None
        if start:
            self.start()

    def start(self):
        debug("debugHttpServer", "httpServer", "starting")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.reuse:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        for port in self.ports:
            try:
                debug("debugHttpServer", "trying port", port)
                self.socket.bind(("", port))
                self.port = port
                debug("debugHttpServer", "opened socket on port", self.port)
                break
            except OSError:
                pass
        if self.port:
            self.socket.listen(1)
            startThread("httpserver", self.getRequests)
            if self.block:
                block()
            return self.port
        else:
            self.socket.close()
            log("httpServer", "unable to find an available port")
            return 0

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
        debugRequest("debugHttpServer", addr, request)
        # send it to the request handler
        response = HttpResponse("HTTP/1.0", 200, {}, None)
        try:
            self.handler(request, response, *self.args)
        except Exception as ex:
            logException("exception in request handler", ex)
            response.status = 500
            response.data = str(ex)+"\n"
        self.sendResponse(client, response)
        debugResponse("debugHttpServer", addr, response)
        client.close()

    def parseRequest(self, client, request):
        clientFile = client.makefile()
        # start a new request
        (request.method, uri, request.protocol) = fixedList(urllib.parse.unquote(clientFile.readline()).strip("\n").split(" "), 3, "")
        # parse the path string into components
        try:
            (pathStr, queryStr) = uri.split("?")
            request.query = dict([fixedList(queryItem.split("="), 2) for queryItem in queryStr.split("&")])
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
            request.data = urllib.parse.unquote(clientFile.read(int(request.headers["Content-Length"])))
        except KeyError:
            request.data = None
        clientFile.close()

    def sendResponse(self, client, response):
        clientIp = client.getpeername()[0]
        if response.data:
            response.headers["Content-Length"] = len(response.data)
        else:
            response.headers["Content-Length"] = 0
        response.headers["Connection"] = "close"
        try:
            reason = http.client.responses[response.status]
        except KeyError:
            reason = ""
        try:
            client.send(bytes(response.protocol+" "+str(response.status)+" "+reason+"\n", "utf-8"))
            for header in response.headers:
                client.send(bytes(header+": "+str(response.headers[header])+"\n", "utf-8"))
            client.send(bytes("\n", "utf-8"))
            if response.data:
                if isinstance(response.data, str):
                    client.send(bytes(response.data, "utf-8"))
                else:
                    client.send(response.data)
        except BrokenPipeError:     # can't do anything about this
            log("sendResponse", "broken pipe", clientIp)
            return
