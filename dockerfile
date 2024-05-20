FROM python:3.11

# Set the working directory to /app
WORKDIR /app

ENV RYE_HOME="/opt/rye"
ENV PATH="$RYE_HOME/shims:$PATH"
ENV RYE_INSTALL_OPTION="--yes"
ENV RYE_TOOLCHAIN="/usr/local/bin/python"
ENV RYE_VERSION=0.33.0

RUN curl -sSf https://rye-up.com/get > /tmp/get-rye.sh
RUN bash /tmp/get-rye.sh
RUN rm /tmp/get-rye.sh
RUN echo 'source "$HOME/.rye/env"' >> ~/.bashrc

RUN rye config --set-bool behavior.use-uv=true
RUN rye config --set-bool behavior.global-python=true
RUN rye config --set default.dependency-operator="~="

COPY . /app
RUN make quicksync