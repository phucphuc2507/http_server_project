import socket
import threading
import os

TFTP_PORT = 69
TFTP_ROOT = "./uploads"
BUFFER_SIZE = 516  # 512 bytes data + 4 bytes header

def handle_request(data, addr, sock):
    opcode = data[1]
    if opcode == 1:  # Read Request (RRQ)
        filename = data[2:].split(b'\0')[0].decode()
        filepath = os.path.join(TFTP_ROOT, filename)
        if not os.path.isfile(filepath):
            return
        with open(filepath, "rb") as f:
            block = 1
            while True:
                chunk = f.read(512)
                packet = b"\x00\x03" + block.to_bytes(2, "big") + chunk
                sock.sendto(packet, addr)
                if len(chunk) < 512:
                    break
                block = (block + 1) % 65536
    elif opcode == 2:  # Write Request (WRQ)
        filename = data[2:].split(b'\0')[0].decode()
        filepath = os.path.join(TFTP_ROOT, filename)
        with open(filepath, "wb") as f:
            ack = b"\x00\x04\x00\x00"
            sock.sendto(ack, addr)
            while True:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                block = data[2:4]
                chunk = data[4:]
                f.write(chunk)
                ack = b"\x00\x04" + block
                sock.sendto(ack, addr)
                if len(chunk) < 512:
                    break

def start_tftp_server():
    if not os.path.exists(TFTP_ROOT):
        os.makedirs(TFTP_ROOT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', TFTP_PORT))
    print(f"[TFTP] Server started on port {TFTP_PORT}")
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        threading.Thread(target=handle_request, args=(data, addr, sock)).start()

if __name__ == "__main__":
    start_tftp_server()
