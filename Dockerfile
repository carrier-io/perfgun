FROM java:alpine

WORKDIR /opt

ENV GATLING_VERSION 2.3.1

RUN mkdir -p gatling
RUN mkdir -p jarvis

COPY setup.py /opt/jarvis
COPY rp_client_3.2.zip /opt/jarvis

RUN apk add --update bash wget python python-dev py-pip libffi-dev openssl-dev build-base && \
  pip install --upgrade pip && \
  pip install /opt/jarvis/rp_client_3.2.zip 'Flask==1.0.2' 'pyyaml==3.13' 'jira==2.0.0' 'flask_restful==0.3.6' 'configobj==5.0.6' 'requests==2.19.1' 'kombu==4.2.1' 'common==0.1.2' 'influxdb==5.2.0' 'argparse==1.4.0' && \
  rm -rf /tmp/*

RUN apk add --update wget bash && \
  mkdir -p /tmp/downloads && \
  wget -q -O /tmp/downloads/gatling-$GATLING_VERSION.zip \
  https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/$GATLING_VERSION/gatling-charts-highcharts-bundle-$GATLING_VERSION-bundle.zip && \
  mkdir -p /tmp/archive && cd /tmp/archive && \
  unzip /tmp/downloads/gatling-$GATLING_VERSION.zip && \
  mv /tmp/archive/gatling-charts-highcharts-bundle-$GATLING_VERSION/* /opt/gatling/ && \
  rm -rf /tmp/*

COPY executor.sh /opt/jarvis
COPY logparser.py /opt/jarvis
COPY config.yaml /tmp/

WORKDIR  /opt/gatling

VOLUME ["/opt/gatling/conf", "/opt/gatling/results", "/opt/gatling/user-files"]

ENV PATH /opt/gatling/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV GATLING_HOME /opt/gatling

COPY tests /opt/gatling
COPY logback.xml /opt/gatling/conf

RUN ["/bin/bash", "-c", "/opt/gatling/bin/gatling.sh -s carrier.WarmUp"]
RUN rm -rf /opt/gatling/results/*

ENTRYPOINT ["gatling.sh"]