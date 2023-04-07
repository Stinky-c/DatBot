FROM python:3.11.2-slim AS install
ARG APT_INSTALL_REMOVABLE="curl"
ARG APT_INSTALL=""
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends $APT_INSTALL $APT_INSTALL_REMOVABLE \
    && apt-get autoremove -y
RUN pip install --upgrade pip
WORKDIR /app/


ENV POETRY_HOME="/opt/poetry"
RUN curl https://install.python-poetry.org/ > get-poetry.py
RUN python get-poetry.py

FROM install AS app-image
ARG INSTALL_ARGS="--no-root --only main"
WORKDIR /app/
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
COPY pyproject.toml .

RUN poetry config virtualenvs.create false \
    && poetry install $INSTALL_ARGS \
    && python get-poetry.py --uninstall \
    && rm get-poetry.py

RUN apt-get purge -y $INSTALL_REMOVABLE \
    && apt-get clean -y \
    && rm -rf /root/.cache \
    && rm -rf /var/apt/lists/* \
    && rm -rf /var/cache/apt/*


# copy and start
FROM app-image as run-image
WORKDIR /app/
COPY src/ .
CMD [ "python", "main.py" ]