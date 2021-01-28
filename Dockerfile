# We suggest using the major.minor tag, not major.minor.patch.
FROM python:3


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

# Setup Python deps
# NOTE: this is created by pipfile-requirements (see Makefile)
ADD requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Sets the container's working directory to /app
WORKDIR /app/
# Copies all files from our local project into the container
ADD . /app/

# runs the pip install command for all packages listed in the requirements.txt file
# RUN pip install pipenv
# RUN pipenv shell
# RUN pipenv install .

EXPOSE 8000