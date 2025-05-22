import socket
import threading
import os
import json
from urllib.parse import unquote, urlparse, parse_qs
from datetime import datetime

UPLOAD_DIR = "uploads"
TEMPLATE_DIR = "templates"
USER_FILE = "users.json"
LOG_FILE = "log.txt"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load users from file
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Save users to file
def save_users(users):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# Ghi log hoạt động
def log_action(ip, name, action):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{time}] {ip} ({name}): {action}\n")

# Đọc file html
def render_template(filename):
    path = os.path.join(TEMPLATE_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def handle_client(sock, addr):
    ip = addr[0]
    users = load_users()
    name = users.get(ip, None)

    try:
        data = sock.recv(65536).decode(errors='ignore')
        if not data:
            sock.close()
            return

        lines = data.splitlines()
        if len(lines) == 0:
            sock.close()
            return

        method, path, *_ = lines[0].split()

        # Route xử lý POST /save-name
        if method == "POST" and path == "/save-name":
            body = data.split("\r\n\r\n", 1)[1]
            params = parse_qs(body)
            user_name = params.get("name", [""])[0]
            user_ip = params.get("ip", [""])[0]
            users[user_ip] = user_name
            save_users(users)
            log_action(user_ip, user_name, "Đăng ký tên truy cập")
            sock.sendall(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
            sock.close()
            return

        # Nếu chưa có tên thì hiện trang nhập tên
        if not name:
            content = render_template("name.html").replace("__IP__", ip)
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + content
            sock.sendall(response.encode('utf-8'))
            sock.close()
            return

        # Tải file từ thư mục uploads
        if method == "GET" and path.startswith("/uploads/"):
            filename = unquote(path[len("/uploads/"):])
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    filedata = f.read()
                header = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename=\"{filename}\"\r\n\r\n"
                sock.sendall(header.encode() + filedata)
                log_action(ip, name, f"Tải xuống {filename}")
            else:
                sock.sendall(b"HTTP/1.1 404 Not Found\r\n\r\nFile not found")
            sock.close()
            return

        # Xóa file
        if method == "GET" and path.startswith("/delete"):
            query = urlparse(path).query
            filename = parse_qs(query).get("filename", [""])[0]
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                log_action(ip, name, f"Đã xóa {filename}")
            sock.sendall(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
            sock.close()
            return

        # Upload file
        if method == "POST" and path == "/upload":
            headers, body = data.split("\r\n\r\n", 1)
            boundary = [line for line in headers.splitlines() if "boundary=" in line][0].split("boundary=")[1]
            boundary = boundary.strip()
            parts = body.split(f"--{boundary}")
            for part in parts:
                if "filename=" in part:
                    header_part, file_data = part.split("\r\n\r\n", 1)
                    file_data = file_data.rstrip("\r\n--")
                    filename_line = [line for line in header_part.splitlines() if "filename=" in line][0]
                    filename = filename_line.split("filename=")[1].strip('"')
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    with open(filepath, 'wb') as f:
                        f.write(file_data.encode('latin1'))  # để giữ nguyên bytes
                    log_action(ip, name, f"Upload file {filename}")
            sock.sendall(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
            sock.close()
            return

        # Trang chính
        if method == "GET" and path == "/":
            content = render_template("index.html")
            file_list = ""
            for f in os.listdir(UPLOAD_DIR):
                link = f"/uploads/{f}"
                delete = f"/delete?filename={f}"
                file_list += f'<li>{f} - <a href="{link}">Tải xuống</a> | <a href="{delete}" onclick="return confirm(\'Xóa?\')">Xóa</a></li>'
            content = content.replace("__USER__", name)
            content = content.replace("__IP__", ip)
            content = content.replace("__FILE_LIST__", file_list)
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + content
            sock.sendall(response.encode('utf-8'))
            sock.close()
            return

        # Không khớp route
        sock.sendall("HTTP/1.1 404 Not Found\r\n\r\nTrang không tồn tại.")
        sock.close()

    except Exception as e:
        print(f"Lỗi xử lý client {ip}: {e}")
        sock.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
        sock.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8080))
    server.listen(5)
    print("Server đang chạy tại http://<your-ip>:8080")

    while True:
        client_sock, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
