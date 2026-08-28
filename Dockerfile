FROM python:3.14-alpine3.24

COPY ./app/ /opt/tracing/app
COPY poetry.lock /opt/tracing/
COPY pyproject.toml /opt/tracing/

WORKDIR /opt/tracing

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false  \
    && poetry install --only main --no-root  --no-interaction \
    && pip uninstall -y poetry \
    && addgroup --gid 1000 tracing \
	&& adduser -D -u 1000 -G tracing tracing \
	&& chown -R 1000:1000 /opt/tracing

USER tracing

EXPOSE 8080

ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8080"]