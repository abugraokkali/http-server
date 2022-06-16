import socket #provides connection between client viz browser here and server
import json #provides json functionality
from urllib.parse import urlsplit, parse_qs
import os #provides os functionality
import re #provides regular expression functionality

class HTTPServer:#The actual HTTP server class.

    status_codes = { #status codes 
        200: 'OK',
        404: 'Not Found',
        301: 'Moved Permanently',
        400: 'Bad Request',
    }

    def __init__(self, host='127.0.0.1', port=8080):#address of server and port of server
        self.host = host
        self.port = port
        self.method = None
        self.uri = None
        self.http_version = '1.1' # default to HTTP/1.1 

    def start(self): #Method for starting the server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#create socket object with IP address and network type
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#SO_REUSEADDR option should be set for all sockets being bound  to the port you want to bind multiple socket onto, not only for new socket.
        s.bind((self.host, self.port))#binds the socket object to the address and port
        s.listen(5)# start listening for connections here atmost 5 connections
        print("Listening at", s.getsockname())
        while True:
            c, addr = s.accept()#accept client requests
            print("Connected by", addr) 
            data = self.recvall(c) #reading just the first 1024 bytes sent by the client.
            response= self.handle_request(data)#handle_request method which will then returns a response
            c.sendall(response)# send back the data to client
            c.close()# close the connection

    def recvall(self, sock):# Helper function to recv all data from a socket
        data = b''
        packet = sock.recv(1024)
        data += packet
        lines = packet.splitlines()
        boundary = None
        for line in lines:
            if b'boundary' in line:
                boundary = line.split(b'=')[1]
                break
        if boundary:
            while True:
                packet = sock.recv(1024)
                if not packet:
                    break
                data += packet
                if boundary + b'--' in packet:
                    break
        return data

    def handle_request(self, data):#handles requests
        lines = data.splitlines()#here we parse the request line to get the method , uri and http version
        request_line = lines[0].split()#request line is the first line of the request
        method, url = request_line[0].decode(), request_line[1].decode()#method is the first element of the request line and url is the second element
        path, query = urlsplit(url).path, urlsplit(url).query
        params = parse_qs(query)

        if(method == 'GET' and path == '/isPrime'):#if the method is GET and the endpoint is /isPrime
            return self.handle_isPrime(params)
        elif(method == 'POST' and path == '/upload'):#if the method is POST and the endpoint is /upload
            return self.handle_upload(data)
        elif(method == 'DELETE' and path == '/remove'):#if the method is DELETE and the endpoint is /remove
            return self.handle_remove(params)
        elif(method == 'PUT' and path == '/rename'):#if the method is DELETE and the endpoint is /remove
            return self.handle_rename(params)
        elif(method == 'GET' and path == '/download'):#if the method is GET and the endpoint is /download
            return self.handle_download(params)
        else:
            return self.response(404, {'error': '404 Request Not found'})

    def handle_isPrime(self, params):
        if "number" not in params:
            return self.response(400, {'error': '400 Bad Request'})
        try:
            number = int(params["number"][0])
            body = {'number': number, 'isPrime': self.is_prime(number)}
            return self.response(200, body)
        except ValueError:
            return self.response(200, {'error': 'Please enter a integer'})

    def is_prime(self,n):
        if(n > 1):
            for i in range(2,n):
                if (n%i) == 0:
                    return False
            return True
        return False
        
    def handle_upload(self, data):
        lines = data.splitlines()
        boundary = ''
        for line in lines:
            if b'boundary' in line:
                boundary = line.split(b'=')[1]
                break
        if boundary == '':
            return self.response(200, {'error': 'Missing file'})  
        b_index = lines.index(b'--' + boundary)
        filename = lines[b_index+1].split(b'filename=')[1].split(b'\r\n')[0].decode().replace('"', '')
        m = re.search(b'Content-Type:(.+?)\r\n\r\n', data)
        with open(filename, 'wb') as f:
            f.write(data.split(m.group(1) + b'\r\n\r\n')[1].split(b'\r\n--' + boundary + b'--')[0])
        return self.response(200, {'message': 'File uploaded successfully'})  

    def handle_remove(self, params):
        if "fileName" not in params:
            return self.response(400, {'error': 'Missing fileName parameter'})
        fileName = params["fileName"][0]
        if os.path.exists(fileName):
            os.remove(fileName)
            return self.response(200, {'message': 'File deleted successfully'})
        else:
            return self.response(200, {'message': 'File does not exist'})
            
    def handle_rename(self, params):
        if "oldFileName" not in params:
            return self.response(400, {'error': 'Missing oldFileName parameter'})
        if "newName" not in params:
            return self.response(400, {'error': 'Missing newName parameter'})

        oldFileName = params["oldFileName"][0]
        if not os.path.exists(oldFileName):
            return self.response(200, {'message': 'File not found'})
        else:
            os.rename(oldFileName, params["newName"][0])
            return self.response(200, {'message': 'File renamed successfully'})

    def handle_download(self, params):
        if "fileName" not in params:
            return self.response(400, {'error': 'Missing fileName parameter'}),
        fileName = params["fileName"][0]
        if not os.path.exists(fileName):
            return self.response(200, {'message': 'File not found'})
        f = open(fileName, "rb")
        return self.response(200, f.read(), 'file')     

    def response(self, status_code, body, type='json'):# returns response line based on status code
        reason = self.status_codes[status_code]#key status returns corresponding values as reason
        response_line = 'HTTP/1.1 %s %s\r\n' % (status_code, reason)
        if type=='json':
            body = json.dumps(body).encode()
        return b''.join([response_line.encode(), b'\r\n', body])#joins all the components together

if __name__ == '__main__':
    server = HTTPServer()
    server.start()