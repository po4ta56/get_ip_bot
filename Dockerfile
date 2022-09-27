FROM python:3.10-alpine3.16
WORKDIR /code
EXPOSE 8000
ENV POETRY_VERSION "~=1.1.4"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN pip install --no-cache poetry${POETRY_VERSION}

COPY poetry.lock pyproject.toml /code/
RUN poetry export -f requirements.txt --output /code/requirements.txt --without-hashes
RUN pip install -r /code/requirements.txt
