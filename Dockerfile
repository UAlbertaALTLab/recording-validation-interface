# We suggest using the major.minor tag, not major.minor.patch.
FROM alpine:latest

# Non-root user for security purposes.
#
# UIDs below 10,000 are a security risk, as a container breakout could result
# in the container being ran as a more privileged user on the host kernel with
# the same UID.
#
# Static GID/UID is also useful for chown'ing files outside the container where
# such a user does not exist.
RUN addgroup -g 10001 -S nonroot && adduser -u 10000 -S -G nonroot -h /home/nonroot nonroot

# Install packages here with `apk add --no-cache`, copy your binary
# into /sbin/, etc.

# Tini allows us to avoid several Docker edge cases, see https://github.com/krallin/tini.
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--", "validation"]
# Replace "myapp" above with your binary

# bind-tools is needed for DNS resolution to work in *some* Docker networks, but not all.
# This applies to nslookup, Go binaries, etc. If you want your Docker image to work even
# in more obscure Docker environments, use this.
RUN apk add --no-cache bind-tools

# Use the non-root user to run our application
USER nonroot

# Sets an environmental variable that ensures output from python is sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1
# Sets the container's working directory to /app
WORKDIR /app/
# Copies all files from our local project into the container
ADD . /app/
# runs the pip install command for all packages listed in the requirements.txt file
RUN pip install .