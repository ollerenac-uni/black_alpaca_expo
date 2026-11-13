# Black Alpaca Expo — 2G GSM privacy demo, slim multi-stage image.
# Supports USRP B210 (SDR_ARGS=type=b200) and RTL-SDR (SDR_ARGS=rtl=0).
#
# Stage 1 builds gr-gsm against Ubuntu's GNU Radio 3.10 and stages its install
# tree. Stage 2 is runtime-only: no compiler/cmake/dev headers, UHD FPGA images
# pruned to B2xx. Cuts the image roughly in half vs a single-stage build.

# ---- Stage 1: build gr-gsm -------------------------------------------------
FROM ubuntu:24.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake pkg-config git ca-certificates \
      gnuradio-dev gr-osmosdr libboost-all-dev pybind11-dev libosmocore-dev \
    && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/ptrkrysik/gr-gsm.git /tmp/gr-gsm \
    && cd /tmp/gr-gsm \
    && git checkout 2ebf07d \
    && cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr \
         -DGR_PYTHON_DIR=/usr/lib/python3/dist-packages \
    && cmake --build build -j"$(nproc)" \
    && DESTDIR=/stage cmake --install build

# ---- Stage 2: runtime ------------------------------------------------------
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
# tshark/wireshark-common must not prompt about setuid dumpcap (we run as root).
RUN echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections
RUN apt-get update && apt-get install -y --no-install-recommends \
      gnuradio gr-osmosdr uhd-host libosmocore-dev rtl-sdr tshark \
      python3 python3-pip python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# gr-gsm install tree from the builder (libs, grgsm_* scripts, python module).
COPY --from=builder /stage/ /
RUN ldconfig
# Fetch ONLY the B2xx (B210) UHD FPGA images — apt's uhd-host ships none, and the
# full set is large. RTL-SDR needs no images, so a download failure is non-fatal.
RUN uhd_images_downloader -t b2xx || echo "WARN: b2xx images not fetched; B210 unusable, RTL-SDR still works"

# GSMEvil2 app + its Python deps in an isolated venv.
WORKDIR /opt/gsmevil2
COPY gsmevil2/ /opt/gsmevil2/
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir scapy   # for replay.py (offline demo)

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
