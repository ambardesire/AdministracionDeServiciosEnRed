from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

host = "192.168.100.10"
port = 8080
authorizer = DummyAuthorizer()
authorizer.add_user("user", "12345", "/archivos/ftps", perm="elradfmw")
authorizer.add_anonymous("/archivos/ftps", perm="elradfmw")

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer((host, port), handler)
server.serve_forever()