# Simple HTTP & TFTP File Server

This is a lightweight Python project that integrates:
- An **HTTP server** for file uploads/downloads through a web interface
- A **TFTP server** for uploading and downloading configuration files using the TFTP protocol
- **User tracking**, including name registration based on IP and activity logging

---

## 🖥 Features

### 🔹 HTTP Server
- Web interface for file upload/download
- Track user names by IP address on first access
- Show uploaded files with uploader name
- Delete uploaded files via the browser
- Styled using CSS for better user experience

### 🔹 TFTP Server
- Receive and send configuration files (`.cfg`, `.txt`, etc.)
- Upload/download via TFTP client (e.g., CLI: `tftp`)
- Shared upload directory with HTTP interface
- Fully compatible with standard TFTP clients

### 🔹 Logging
- Logs all upload/download actions with timestamps and IP address

---

## 📁 Project Structure

