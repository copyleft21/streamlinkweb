FROM python:3.9-alpine3.14 as base
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1
RUN apk update && apk add --no-cache ffmpeg libxslt-dev libxml2-dev

FROM base as builder
RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN python3 -m pip wheel --wheel-dir=/root/wheels streamlink

FROM base as python-deps
RUN pip install pipenv
RUN apk add --no-cache --virtual gcc
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM base
COPY --from=builder /root/wheels /root/wheels
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
RUN pip install --no-index --find-links=/root/wheels streamlink
RUN addgroup -S streamlinkweb && adduser -S streamlinkweb -G streamlinkweb
WORKDIR /home/streamlinkweb
USER streamlinkweb
COPY streamlinkweb .

EXPOSE 4449/tcp
ENTRYPOINT ["python3", "main.py"]