# We suggest using the major.minor tag, not major.minor.patch.
FROM python:3.7


# Choose an ID that will be consistent across all machines in the network
# To avoid overlap with user IDs, use an ID over
# /etc/login.defs:/UID_MAX/, which defaults to 60,000
ARG UID_GID=60002
ARG WSGI_USER=revcal
# Create the user/group for the application
RUN groupadd --system --gid ${UID_GID} ${WSGI_USER} \
 && useradd --no-log-init --system --gid ${WSGI_USER} --uid ${UID_GID} ${WSGI_USER}

# Sets an environmental variable that ensures output from python is sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH=/root/.cargo/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN pip install maturin pep517 pipenv

# Sets the container's working directory to /app
WORKDIR /app/

COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock
RUN pipenv install --system --dev

# Copies all files from our local project into the container
COPY . /app/
COPY crk.zhfst /app/
RUN mkdir static && python manage.py collectstatic

EXPOSE 8000

RUN chown "${WSGI_USER}:${WSGI_USER}" /app
USER  ${WSGI_USER}:${WSGI_USER}
ENV UWSGI_HTTP=:8000 UWSGI_MASTER=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_AUTO_CHUNKED=1 UWSGI_WSGI_ENV_BEHAVIOUR=holy
CMD ["uwsgi", "-w", "recvalsite.wsgi", "--static-map", "/static=/var/www/recvalsite/static"]
