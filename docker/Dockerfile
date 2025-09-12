FROM ubuntu:24.04

ARG TARGETPLATFORM
ARG DEBIAN_FRONTEND=noninteractive

USER root

#### copy application
COPY app /opt/app

RUN \
    #### base update & packages
    apt-get update -y \
      && apt-get dist-upgrade -y \
      && apt-get install -y tzdata \
      && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
      && dpkg-reconfigure -f noninteractive tzdata \
    #### install dependencies
    && apt-get install -y python3 python3-pip \
      && pip3 install -r /opt/app/requirements.txt \
    #### cleanup
    && apt-get clean && apt-get autoremove -y \
      && rm -rf /var/lib/apt/lists/* \
      && find /var/log/ -type f -exec cp /dev/null {} \;

USER 65534

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/gunicorn", "-w", "1", "-c", "/opt/app/gunicorn.conf.py", "--bind", "0.0.0.0:8080", "--chdir", "/opt/app", "wsgi:app"]
