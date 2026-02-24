FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY configdiff/ configdiff/

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

COPY --from=builder /install /usr/local

RUN groupadd --gid 1000 configdiff \
    && useradd --uid 1000 --gid configdiff --shell /bin/false configdiff

USER configdiff
WORKDIR /data

ENTRYPOINT ["configdiff"]
CMD ["--help"]
