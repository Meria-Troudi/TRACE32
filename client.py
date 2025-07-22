# client.py
import socket

HOST, PORT = "127.0.0.1", 12345

def main():
    with socket.create_connection((HOST, PORT)) as s:
        while True:
            cmd = input("Enter RUN_CMM or quit> ")
            if cmd.lower()=="quit":
                break
            s.sendall((cmd+"\n").encode())
            resp = s.recv(8192).decode().strip()
            print("[Client] ←", resp)

if __name__=="__main__":
    main()
