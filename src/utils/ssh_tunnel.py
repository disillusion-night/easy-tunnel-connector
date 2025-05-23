import threading
import paramiko
import socket
import select
from socketserver import ThreadingTCPServer, StreamRequestHandler

class SocksProxy(StreamRequestHandler):
    def handle(self):
        # 只支持SOCKS5 CONNECT
        try:
            data = self.request.recv(262)
            if data[0] != 0x05:
                self.request.close()
                return
            # 握手应答
            self.request.sendall(b'\x05\x00')
            data = self.request.recv(4)
            if len(data) < 4 or data[1] != 0x01:
                self.request.close()
                return
            addrtype = data[3]
            if addrtype == 1:  # IPv4
                addr = socket.inet_ntoa(self.request.recv(4))
            elif addrtype == 3:  # 域名
                domain_len = self.request.recv(1)[0]
                addr = self.request.recv(domain_len)
                addr = addr.decode()
            else:
                self.request.close()
                return
            port = int.from_bytes(self.request.recv(2), 'big')
            # 通过SSH打开通道
            try:
                chan = self.server.ssh_transport.open_channel(
                    'direct-tcpip', (addr, port), self.request.getpeername())
            except Exception as e:
                self.request.close()
                return
            if chan is None:
                self.request.close()
                return
            # 通知客户端连接成功
            self.request.sendall(b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + b'\x00\x00')
            while True:
                r, w, x = select.select([self.request, chan], [], [])
                if self.request in r:
                    d = self.request.recv(1024)
                    if len(d) == 0:
                        break
                    chan.send(d)
                if chan in r:
                    d = chan.recv(1024)
                    if len(d) == 0:
                        break
                    self.request.send(d)
            chan.close()
            self.request.close()
        except Exception:
            self.request.close()


def create_ssh_tunnel(ssh_host, ssh_port, ssh_username, ssh_password, local_bind_address=('127.0.0.1', 1080), keepalive=30):
    """
    启动本地SOCKS5代理并通过SSH动态端口转发
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ssh_host, port=ssh_port, username=ssh_username, password=ssh_password)
    transport = client.get_transport()
    transport.set_keepalive(keepalive)

    class SocksServer(ThreadingTCPServer):
        allow_reuse_address = True

    server = SocksServer(local_bind_address, SocksProxy)
    server.ssh_transport = transport
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    server.local_bind_port = local_bind_address[1]
    server.stop = server.shutdown
    return server
