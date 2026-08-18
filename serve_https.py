import http.server
import ssl
import sys

class SimpleHTTPServer:
    def __init__(self, port=8443, certfile='cert.pem', keyfile='key.pem'):
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile

    def start(self):
        server_address = ('0.0.0.0', self.port)
        httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        
        print(f"HTTPS Server active on port {self.port}")
        httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8443
    server = SimpleHTTPServer(port=port)
    server.start()
