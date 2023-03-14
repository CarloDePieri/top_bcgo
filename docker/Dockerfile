FROM python
LABEL project=top_bgco
ENV container="docker" DOCKER_VIRTUALENV_CACHE=/top_bgco-cache

# Install always needed dependencies: poetry and invoke
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    echo ". $HOME/.poetry/env" >> /root/.bashrc && \
    pip3 install invoke

# Use the pyproject.toml as sentinel: if it doesn't change, docker will be able to cache the layer that contains
# all virtualenv dependencies.
# Cached layers can be skipped with `docker build --no-cache` or `docker-compose build --no-cache`.
# They can be deleted, after deleting the main image with docker or docker-compose, by running 
# `docker builder prune --filter label=project=top_bgco`.
WORKDIR /top_bgco
ADD https://raw.githubusercontent.com/CarloDePieri/top_bcgo/main/pyproject.toml .
RUN export PATH=$HOME/.local/bin:$PATH && \
  # Simulate an empty backend module, since poetry will try to install it \
  mkdir top_bcgo && \
  touch top_bcgo/__init__.py && \
  # Actually install all dependencies; the virtualenv is not created in the project dir \
  poetry install && \
  # Prepare the cache folder and move everything from this one there \
  mkdir $DOCKER_VIRTUALENV_CACHE && \
  mv * $DOCKER_VIRTUALENV_CACHE/.

# This is the final layer containing the source code
RUN git clone https://github.com/CarloDePieri/top_bcgo.git . && \
  mv $DOCKER_VIRTUALENV_CACHE/poetry.lock . && \
  export PATH=$HOME/.local/bin:$PATH && \
  cd /top_bgco && \
  poetry run python populate_db.py
