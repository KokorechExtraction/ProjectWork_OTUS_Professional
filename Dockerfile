FROM python:3.13-slim

WORKDIR /code
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /code/
RUN pip install --upgrade pip && pip install .

COPY . /code

RUN chmod +x /code/scripts/start.sh

CMD ["/code/scripts/start.sh"]
