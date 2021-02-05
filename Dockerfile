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
RUN /bin/bash -c "source $HOME/.cargo/env"

RUN pip install maturin
RUN pip install pep517
RUN pip install pipenv 

# Sets the container's working directory to /app
WORKDIR /app/
# Copies all files from our local project into the container
ADD . /app/

RUN pipenv install --system --deploy --ignore-pipfile

# runs the pip install command for all packages listed in the requirements.txt file
# RUN pip install -r /app/requirements.txt

EXPOSE 8000