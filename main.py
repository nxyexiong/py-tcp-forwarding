import socket
import select
import threading
import time
import sys

class Conn:
 def __init__(self, fd, target_addr):
  self.remote_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  self.remote_fd.connect(target_addr)
  self.client_fd = fd
  self.run_thread = None
  self.running = False

 def run(self):
  self.running = True
  self.run_thread = threading.Thread(target=self.handle_recv)
  self.run_thread.start()

 def close(self):
  self.running = False
  if self.run_thread is not None:
   while self.run_thread.is_alive():
    time.sleep(1)

 def handle_recv(self):
  while self.running:
   readable, _, _ = select.select([self.remote_fd, self.client_fd], [], [], 1)
   if not readable:
    continue
   for s in readable:
    if s is self.remote_fd:
     data = self.remote_fd.recv(2048)
     if data and len(data) > 0:
      while len(data) > 0:
       sent = self.client_fd.send(data)
       data = data[sent:]
     else:
      self.running = False
      break
    if s is self.client_fd:
     data = self.client_fd.recv(2048)
     if data and len(data) > 0:
      while len(data) > 0:
       sent = self.remote_fd.send(data)
       data = data[sent:]
     else:
      self.running = False
      break
  self.client_fd.close()
  self.remote_fd.close()
  print('client closed')

class Server:
 def __init__(self, listen_port, target_addr):
  self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  self.sock.bind(('', listen_port))
  self.sock.listen()
  self.target_addr = target_addr
  self.run_thread = None
  self.conn_list = []
  self.running = False

 def run(self):
  self.running = True
  self.run_thread = threading.Thread(target=self.handle_accept)
  self.run_thread.start()

 def close(self):
  self.running = False
  for conn in self.conn_list:
   conn.close()
  if self.run_thread is not None:
   while self.run_thread.is_alive():
    time.sleep(1)
  self.sock.close()

 def handle_accept(self):
  while self.running:
   readable, _, _ = select.select([self.sock, ], [], [], 1)
   if not readable:
    continue
   fd, addr = self.sock.accept()
   print(f"new conn: {addr}")
   conn = Conn(fd, self.target_addr)
   conn.run()
   self.conn_list.append(conn)

if __name__ == '__main__':
 args = sys.argv
 listen_port = None
 dst_ip = None
 dst_port = None
 if len(args) < 4:
  print("wrong args, use: <listen_port> <dst_ip> <dst_port>")
  sys.exit(1)
 try:
  listen_port = int(args[1])
  dst_ip = str(args[2]).encode('utf-8')
  dst_port = int(args[3])
 except Exception:
  print("wrong arg type")
  sys.exit(1)
 server = Server(listen_port, (dst_ip, dst_port))
 server.run()
 while True:
  try:
   time.sleep(1)
  except KeyboardInterrupt:
   print("terminating...")
   server.close()
   break


