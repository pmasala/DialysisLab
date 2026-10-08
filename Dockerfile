# Official CPython 3.12.14 / Debian trixie, pinned by content digest.
FROM python@sha256:7a8b475003c4fe15a2cd4e55e5cfc2f3560bdc9333d624f24cdd6d4340fd7a17 AS build
RUN printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260824T000000Z trixie main\n' > /etc/apt/sources.list \
    && rm /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends g++=4:14.2.0-1 cmake=3.31.6-2 make=4.4.1-2 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/dialysislab
COPY CMakeLists.txt gui_dependencies.json ./
COPY cmake/ cmake/
COPY src/ src/
COPY python/ python/
COPY scenarios/ scenarios/
COPY tools/build_identity.py tools/fetch_gui.py tools/
ARG SOURCE_REVISION=unavailable
ENV SOURCE_REVISION=${SOURCE_REVISION}
RUN cmake -S . -B /opt/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /opt/build --parallel 3 \
    && dpkg-query -W > /opt/build/build-packages.txt

FROM python@sha256:7a8b475003c4fe15a2cd4e55e5cfc2f3560bdc9333d624f24cdd6d4340fd7a17 AS runtime
ENV PYTHONPATH=/opt/dialysislab/python PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/dialysislab
COPY --from=build /opt/build/plant /opt/build/control /opt/build/protection /opt/build/build_identity.json /opt/build/build-packages.txt /opt/bin/
COPY python/ python/
COPY scenarios/ scenarios/
COPY LICENSE ./LICENSE
RUN mkdir -p /run/dialysis/admin /run/dialysis/control /run/dialysis/protection /run/dialysis/patient /run/dialysis/device /results \
    && chown -R 10001:10001 /run/dialysis /results \
    && dpkg-query -W > /opt/bin/runtime-packages.txt
USER 10001:10001

# Optional GUI target; the core runtime does not load graphical libraries.
FROM build AS gui-build
RUN printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260824T000000Z trixie main\n' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends libx11-dev=2:1.8.12-1 libxext-dev=2:1.3.4-1+b3 \
    && rm -rf /var/lib/apt/lists/*
RUN python3 tools/fetch_gui.py --cache /opt/gui-deps \
    && cmake -S . -B /opt/gui-build -DCMAKE_BUILD_TYPE=Release -DDIALYSISLAB_GUI=ON -DDIALYSISLAB_GUI_DEPS=/opt/gui-deps \
    && cmake --build /opt/gui-build --parallel 3 \
    && dpkg-query -W > /opt/gui-build/build-packages.txt

FROM runtime AS gui-runtime
USER 0:0
RUN printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260824T000000Z trixie main\n' > /etc/apt/sources.list \
    && rm /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends libx11-6=2:1.8.12-1 libxext6=2:1.3.4-1+b3 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /captures && chown 10001:10001 /captures
COPY --from=gui-build /opt/gui-build/device-ui /opt/gui-build/plant /opt/gui-build/control /opt/gui-build/protection /opt/gui-build/build_identity.json /opt/gui-build/build-packages.txt /opt/bin/
COPY gui_dependencies.json ./
COPY docs/dependencies/GUI_NOTICES.md /opt/dialysislab/GUI_NOTICES.md
RUN dpkg-query -W > /opt/bin/runtime-packages.txt
USER 10001:10001
