FROM python:3.10.9-slim AS install
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends curl ffmpeg \
    && apt-get autoremove -y
RUN pip install --upgrade pip
WORKDIR /app/


ENV POETRY_HOME="/opt/poetry"
RUN curl https://install.python-poetry.org/ > get-poetry.py
RUN python get-poetry.py

FROM install AS app-image
ARG INSTALL_ARGS="--no-root --no-dev"
WORKDIR /app/
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false \
    && poetry install $INSTALL_ARGS \
    && python get-poetry.py --uninstall \
    && rm get-poetry.py

RUN apt-get purge -y curl \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/*


# copy and start
FROM app-image as run-image
WORKDIR /app/
COPY src/ .
CMD [ "python", "main.py" ]