# Official CPython 3.12.14 / Debian trixie, pinned by content digest.
FROM python@sha256:7a8b475003c4fe15a2cd4e55e5cfc2f3560bdc9333d624f24cdd6d4340fd7a17 AS build
RUN printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260824T000000Z trixie main\n' > /etc/apt/sources.list \
    && rm /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends g++=4:14.2.0-1 cmake=3.31.6-2 make=4.4.1-2 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/dialysislab
COPY CMakeLists.txt ./
COPY src/ src/
COPY python/ python/
COPY scenarios/ scenarios/
COPY tools/build_identity.py tools/build_identity.py
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
