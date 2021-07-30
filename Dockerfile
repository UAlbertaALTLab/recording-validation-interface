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
 && mkdir -p /var/www/recvalsite \
 && chown ${WSGI_USER}:${WSGI_USER} /app /var/www/recvalsite

RUN apt-get update -qq && apt-get -y install \
      autoconf \
      automake \
      build-essential \
      cmake \
      git-core \
      libass-dev \
      libfreetype6-dev \
      libtool \
      libvorbis-dev \
      libxcb1-dev \
      pkg-config \
      texinfo \
      wget \
      zlib1g-dev \
      nasm \
      yasm \
      libx265-dev \
      libnuma-dev \
      libvpx-dev \
      libmp3lame-dev \
      libopus-dev \
      libx264-dev \
      libfdk-aac-dev
RUN mkdir -p ~/ffmpeg_sources ~/bin && cd ~/ffmpeg_sources && \
    wget -O ffmpeg-4.2.2.tar.bz2 https://ffmpeg.org/releases/ffmpeg-4.2.2.tar.bz2 && \
    tar xjvf ffmpeg-4.2.2.tar.bz2 && \
    cd ffmpeg-4.2.2 && \
    PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
      --prefix="$HOME/ffmpeg_build" \
      --pkg-config-flags="--static" \
      --extra-cflags="-I$HOME/ffmpeg_build/include" \
      --extra-ldflags="-L$HOME/ffmpeg_build/lib" \
      --extra-libs="-lpthread -lm" \
      --bindir="$HOME/bin" \
      --enable-libfdk-aac \
      --enable-gpl \
      --enable-libass \
      --enable-libfreetype \
      --enable-libmp3lame \
      --enable-libopus \
      --enable-libvorbis \
      --enable-libvpx \
      --enable-libx264 \
      --enable-libx265 \
      --enable-nonfree && \
    PATH="$HOME/bin:$PATH" make -j8 && \
    make install -j8 && \
    hash -r
RUN mv ~/bin/ffmpeg /usr/local/bin && mv ~/bin/ffprobe /usr/local/bin && mv ~/bin/ffplay /usr/local/bin

USER ${WSGI_USER}:${WSGI_USER}
WORKDIR /app/

# Copies all files from our local project into the container
COPY --from=builder --chown=${WSGI_USER}:${WSGI_USER} /app/.venv /app/.venv
COPY --chown=${WSGI_USER}:${WSGI_USER} . .

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
RUN python manage.py collectstatic

EXPOSE 8000
ENV UWSGI_HTTP=:8000 UWSGI_MASTER=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_AUTO_CHUNKED=1 UWSGI_WSGI_ENV_BEHAVIOUR=holy
CMD ["uwsgi", "-w", "recvalsite.wsgi", "--processes", "10", "--static-map", "/static=/var/www/recvalsite/static"]
