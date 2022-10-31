import socket
import urllib.parse
from rutifu import *
from .httpClasses import *

class HttpClient(object):
    def __init__(self, host, port=80):
        self.host = host
        self.port = port

    def get(self, path, query={}, headers={}):
        return self.sendRequest(HttpRequest("GET", path, query, "HTTP/1.0", headers))

    def put(self, path, query={}, headers={}, data=None):
        return self.sendRequest(HttpRequest("PUT", path, query, "HTTP/1.0", headers, data))

    def post(self, path, query={}, headers={}, data=None):
        return self.sendRequest(HttpRequest("POST", path, query, "HTTP/1.0", headers, data))

    def delete(self, path, query={}, headers={}):
        return self.sendRequest(HttpRequest("DELETE", path, query, "HTTP/1.0", headers))

    def sendRequest(self, request):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            addr = self.host+":"+str(self.port)
            self.socket.connect((self.host, self.port))
            debug("debugHttpClient", "opened socket to", addr)
            # send the request
            uri = request.path
            sep = "?"
            for query in request.query:
                uri += sep
                uri += query+"="+request.query[query]
                sep = "&"
            msg = request.method+" "+urllib.parse.quote(uri)+" "+request.protocol+"\n"
            for header in request.headers:
                msg += header+": "+request.headers[header]+"\n"
            if request.data:
                msg += "Content-Length: "+str(len(request.data))+"\n"
                msg += "\n"
                msg += request.data
            else:
                msg += "\n"
            debugRequest("debugHttpClient", addr, request)
            self.socket.sendall(bytes(msg, "utf-8"))
            # read the response
            serverFile = self.socket.makefile()
            (protocol, status) = fixedList(serverFile.readline().strip("\n").split(" "), 2, "")
            headers = {}
            (headerName, headerValue) = fixedList(serverFile.readline().strip("\n").split(":"), 2, "")
            while headerName != "":
                headers[headerName.strip()] = headerValue.strip()
                (headerName, headerValue) = fixedList(serverFile.readline().strip("\n").split(":"), 2, "")
            # read the data
            try:
                data = serverFile.read(int(headers["Content-Length"]))
            except KeyError:
                data = None
            try:
                status = int(status)
            except ValueError:
                log("httpClient", addr, "bad status:", status, "protocol:", protocol)
                status = 0
            response = HttpResponse(protocol, int(status), headers, data)
            debugResponse("debugHttpClient", addr, response)
            serverFile.close()
            self.socket.close()
            return response
        except Exception as ex:
            # logException("httpClient "+addr, ex)
            return HttpResponse("", 0, {}, str(ex))
