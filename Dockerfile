# Dùng Node.js base image (Debian)
FROM --platform=linux/amd64 node:20-bullseye-slim

# Cài đặt các thư viện hệ thống cần thiết cho Blender headless
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libgl1-mesa-dev \
    libxi6 \
    libxrender1 \
    libxkbcommon-x11-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY blender-5.1.0-linux-x64.tar.xz /tmp/blender.tar.xz

# Giải nén và setup đường dẫn
RUN tar -xf /tmp/blender.tar.xz -C /opt/ \
    && rm /tmp/blender.tar.xz \
    && mv /opt/blender-* /opt/blender \
    && ln -s /opt/blender/blender /usr/local/bin/blender

# Thiết lập thư mục làm việc cho Node app
WORKDIR /app

# Copy file cấu hình Node và cài package
COPY package.json ./
RUN npm install

# Copy toàn bộ code vào container
COPY . .

# Mở port 3000 cho API
EXPOSE 3000

# Khởi chạy server
CMD ["node", "server.js"]