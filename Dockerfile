FROM python:3.9 as builder

ENV POETRY_VIRTUALENVS_IN_PROJECT="true"

WORKDIR /www/backend

RUN curl -sSL https://install.python-poetry.org | python3

COPY poetry.lock pyproject.toml /www/backend/

RUN ~/.local/bin/poetry install

FROM python:3.9-slim

MAINTAINER jsclndnz@gmail.com

WORKDIR /www/backend

COPY --from=builder /www/backend/.venv /www/backend/.venv

COPY . /www/backend

ENV PATH="/www/backend/.venv/bin:$PATH"

EXPOSE 80

ENTRYPOINT ["uvicorn", "app:app", "--port", "80", "--host", "0.0.0.0"]