FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Tokyo

# Essentials
RUN apt-get update && apt-get install -y python3-pip tzdata cron vim tmux

# Python modules
RUN pip3 install --upgrade pip
RUN pip3 install slackbot slack_bolt

# Remove caches
RUN rm -rf /var/lib/apt/lists/*
