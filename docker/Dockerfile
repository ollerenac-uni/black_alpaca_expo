# Black Alpaca Expo — 2G GSM privacy demo, all-in-one image.
# GNU Radio 3.10 + UHD + gr-osmosdr + libosmocore from Ubuntu apt; gr-gsm built
# from source (pinned); GSMEvil2 in a venv. Runs livemon_headless + GSMEvil2.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# tshark/wireshark-common must not prompt about setuid dumpcap (we run as root).
RUN echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake pkg-config git ca-certificates \
      gnuradio gnuradio-dev gr-osmosdr \
      libuhd-dev uhd-host \
      libosmocore-dev \
      pybind11-dev \
      libboost-all-dev \
      rtl-sdr \
      tshark \
      python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# gr-gsm (pinned to the commit verified on bare metal: 23/23 ctest).
RUN git clone https://github.com/ptrkrysik/gr-gsm.git /tmp/gr-gsm \
    && cd /tmp/gr-gsm \
    && git checkout 2ebf07d \
    && cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr \
    && cmake --build build -j"$(nproc)" \
    && cmake --install build \
    && ldconfig \
    && rm -rf /tmp/gr-gsm

# UHD FPGA images for the B210 (no-op for RTL-SDR; don't fail build if offline).
RUN uhd_images_downloader || true

# GSMEvil2 app + its Python deps in an isolated venv.
WORKDIR /opt/gsmevil2
COPY gsmevil2/ /opt/gsmevil2/
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
