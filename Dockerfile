FROM python:3.11-slim-bookworm

ARG BLENDER_VERSION=4.2.11
ARG BLENDER_MAJOR=4.2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    BLENDER_PATH=/opt/blender/blender \
    CONVERT_API_STORAGE=/app/storage

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libdbus-1-3 \
        libegl1 \
        libgl1 \
        libglib2.0-0 \
        libglu1-mesa \
        libice6 \
        libsm6 \
        libwayland-client0 \
        libwayland-cursor0 \
        libwayland-egl1 \
        libx11-6 \
        libxcursor1 \
        libxfixes3 \
        libxi6 \
        libxinerama1 \
        libxkbcommon0 \
        libxrandr2 \
        libxrender1 \
        libxxf86vm1 \
        wget \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN wget -O /tmp/blender.tar.xz "https://download.blender.org/release/Blender${BLENDER_MAJOR}/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && mkdir -p /opt \
    && tar -xJf /tmp/blender.tar.xz -C /opt \
    && mv "/opt/blender-${BLENDER_VERSION}-linux-x64" /opt/blender \
    && rm /tmp/blender.tar.xz

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api_server.py glb_to_usdz.py ./

RUN mkdir -p /app/storage/downloads /app/storage/work

EXPOSE 8000

CMD ["python", "api_server.py"]
