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

RUN pip install maturin
RUN pip install pep517
RUN pip install pipenv

# Sets the container's working directory to /app
WORKDIR /app/
# Copies all files from our local project into the container
ADD . /app/
ADD crk.zhfst /app/

RUN pipenv install --system --ignore-pipfile --dev

EXPOSE 8000