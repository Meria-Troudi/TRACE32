import socket
s = socket.socket()
s.connect(("127.0.0.1", 12345))
print("Connected")
s.sendall(b"RUN_CMM\n")
print("Sent RUN_CMM")
data = s.recv(1024)
print("Received:", data.decode())
s.close()
