#https://habr.com/sandbox/28540/
#https://stackoverflow.com/questions/5975952/how-to-extract-http-message-body-in-basehttprequesthandler-do-post
#https://stackoverflow.com/questions/3788897/how-to-parse-basehttprequesthandler-path

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

class HttpProcessor(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type','text/html')
        self.end_headers()
        
        getPath = self.path
        self.wfile.write("hello ! <br> get path = " + getPath
            + "<form method=post>"
            + "<input type=hidden name=hid value='hidden'>"
            + "<input type=submit value='send'></form>")
        
    def do_POST(self):
        self.send_response(200)
        self.send_header('content-type','text/html')
        self.end_headers()
        
        contentLen = int(self.headers.getheader('content-length', 0))
        postBody = self.rfile.read(contentLen)
        getPath = self.path
        
        self.wfile.write("post RECEIVE!")
        self.wfile.write("<br> get path = " + getPath)
        self.wfile.write("<Br>Post body=")
        self.wfile.write(postBody)
        
        
IP = "0.0.0.0" #os.getenv(IP, "0.0.0.0")
PORT = int("8080") #int(os.getenv(PORT, 8080))
serv = HTTPServer((IP, PORT), HttpProcessor)
serv.serve_forever()
