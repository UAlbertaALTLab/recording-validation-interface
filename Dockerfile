# We suggest using the major.minor tag, not major.minor.patch.
FROM python:3.7 AS builder

# Sets an environmental variable that ensures output from python is sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Add build-time dependencies (i.e., Rust)
ADD https://sh.rustup.rs rustup-init
RUN sh rustup-init -y \
 && pip install maturin pep517 pipenv
ENV PATH="/root/.cargo/bin:${PATH}"


# Install ALL THE PYTHONS
# Place in /app/.venv so we can copy all the built dependencies to the application image
WORKDIR /app/
COPY Pipfile Pipfile.lock ./
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --dev


############################# Application image ##############################

FROM python:3.7

# Choose an ID that will be consistent across all machines in the network
# To avoid overlap with user IDs, use an ID over
# /etc/login.defs:/UID_MAX/, which defaults to 60,000
ARG UID_GID=60004
ARG WSGI_USER=speech-db
# Create the user/group for the application
RUN groupadd --system --gid ${UID_GID} ${WSGI_USER} \
 && useradd --no-log-init --system --gid ${WSGI_USER} --uid ${UID_GID} ${WSGI_USER} \
 && mkdir /app \
 && chown ${WSGI_USER}:${WSGI_USER} /app

USER ${WSGI_USER}:${WSGI_USER}
WORKDIR /app/

# Copies all files from our local project into the container
COPY --from=builder --chown=${WSGI_USER}:${WSGI_USER} /app/.venv /app/.venv
COPY --chown=${WSGI_USER}:${WSGI_USER} . .

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
RUN mkdir static && STATIC_ROOT=/app/static python manage.py collectstatic

EXPOSE 8000
ENV UWSGI_HTTP=:8000 UWSGI_MASTER=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_AUTO_CHUNKED=1 UWSGI_WSGI_ENV_BEHAVIOUR=holy
CMD ["uwsgi", "-w", "recvalsite.wsgi", "--static-map", "/static=/var/www/recvalsite/static"]
