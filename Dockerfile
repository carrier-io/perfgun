FROM openjdk:8-jdk

WORKDIR /opt

ENV GATLING_VERSION 2.3.1
ENV lg_name perfgun
ENV lg_id 1
ARG UNAME=carrier
ARG UID=1001
ARG GID=1001

RUN mkdir -p gatling

COPY rp_client_3.2.zip /tmp

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl build-essential python-dev python-pip git sudo && \
    pip install --upgrade pip && apt-get clean

# Creating carrier user and making him sudoer
RUN groupadd -g $GID $UNAME
RUN useradd -m -u $UID -g $GID -s /bin/bash $UNAME
RUN echo "carrier    ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN pip install setuptools==40.6.2
RUN pip install /tmp/rp_client_3.2.zip 'Flask==1.0.2' 'flask_restful==0.3.6' \
    'configobj==5.0.6' 'requests==2.19.1' 'kombu==4.2.1' 'common==0.1.2' \
    'influxdb==5.2.0' 'argparse==1.4.0' 'numpy==1.15.4' && \
    rm -rf /tmp/*

# Installing Java Jolokia
RUN  mkdir /opt/java && cd /opt/java \
 && wget -O jolokia-jvm-1.6.0-agent.jar \
 http://search.maven.org/remotecontent?filepath=org/jolokia/jolokia-jvm/1.6.0/jolokia-jvm-1.6.0-agent.jar

# Installing Telegraf
RUN cd /tmp && wget https://dl.influxdata.com/telegraf/releases/telegraf_1.8.3-1_amd64.deb && \
    dpkg -i telegraf_1.8.3-1_amd64.deb
COPY telegraf.conf /etc/telegraf/telegraf.conf
COPY jolokia.conf /opt

ENV PATH /opt/gatling/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH

RUN chown -R ${UNAME}:${UNAME} /opt/gatling
RUN chown -R ${UNAME}:${UNAME} /opt/gatling/

# Installting Gatling

USER ${UNAME}

WORKDIR /opt/gatling
ENV GATLING_HOME /opt/gatling

RUN wget -q -O /tmp/gatling-$GATLING_VERSION.zip https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/$GATLING_VERSION/gatling-charts-highcharts-bundle-$GATLING_VERSION-bundle.zip && \
  unzip /tmp/gatling-$GATLING_VERSION.zip && \
  mv gatling-charts-highcharts-bundle-$GATLING_VERSION/* /opt/gatling/ && \
  rm -rf gatling-charts-highcharts-bundle-$GATLING_VERSION


COPY executor.sh /opt/gatling/bin
RUN sudo chmod +x /opt/gatling/bin/executor.sh
COPY logparser.py /opt/gatling/bin
COPY compare_build_metrix.py /opt/gatling/bin
COPY config.yaml /tmp/

WORKDIR  /opt/gatling

VOLUME ["/opt/gatling/conf", "/opt/gatling/results", "/opt/gatling/user-files"]

COPY tests /opt/gatling
COPY logback.xml /opt/gatling/conf

RUN ["/bin/bash", "-c", "/opt/gatling/bin/gatling.sh -s carrier.WarmUp"]
RUN rm -rf /opt/gatling/results/*

ENTRYPOINT ["gatling.sh"]