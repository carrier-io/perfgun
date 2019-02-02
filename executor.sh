#!/bin/bash

export tokenized=$(python -c "from os import environ; print environ['test'].split('.')[1].lower()")
export influx_host=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print y.get('host')")
export influx_port=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print y.get('port',2003)")

if [[ -z "${influx_host}" ]]; then
export influx_piece=""
else
export influx_piece="-Dgatling.data.graphite.host=${influx_host} -Dgatling.data.graphite.port=${influx_port} -Dgatling.data.graphite.rootPathPrefix=${test_type}.${env}.${users}"
sudo sed -i "s/LOAD_GENERATOR_NAME/${lg_name}_${tokenized}_${lg_id}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/INFLUX_HOST/${influx_host}/g" /etc/telegraf/telegraf.conf
sudo service telegraf restart
DEFAULT_EXECUTION="/usr/bin/java"
JOLOKIA_AGENT="-javaagent:/opt/java/jolokia-jvm-1.6.0-agent.jar=config=/opt/jolokia.conf"
DEFAULT_JAVA_OPTS=" -server -Xms1g -Xmx1g -XX:+UseG1GC -XX:MaxGCPauseMillis=30"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -XX:G1HeapRegionSize=16m -XX:InitiatingHeapOccupancyPercent=75"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -XX:+ParallelRefProcEnabled -XX:+PerfDisableSharedMem -XX:+AggressiveOpts"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -XX:+OptimizeStringConcat -XX:+HeapDumpOnOutOfMemoryError"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -Djava.net.preferIPv4Stack=true -Djava.net.preferIPv6Addresses=false "
export GATLING_HOME="/opt/gatling"
export GATLING_CONF="${GATLING_HOME}/conf"
export COMPILER_CLASSPATH="${GATLING_HOME}/lib/*:${GATLING_CONF}:"
export GATLING_CLASSPATH="${GATLING_HOME}/lib/*:${GATLING_HOME}/user-files:${GATLING_CONF}:"
fi

export JAVA_OPTS="-Dgatling.http.ahc.pooledConnectionIdleTimeout=150000 -Dgatling.http.ahc.readTimeout=150000 -Dgatling.http.ahc.requestTimeout=150000 ${influx_piece} -DapiUrl=$url -Dduration=$duration -Dramp_users=$users -Dramp_duration=$rampup_time -Dgatling.data.writers.0=console -Dgatling.data.writers.1=file -Dgatling.data.writers.2=graphite -Dcharting.indicators.lowerBound=2000 -Dcharting.indicators.higherBound=3000"

echo $JAVA_OPTS

cd /opt/gatling/bin

start_time=$(date +%s)000

echo "Starting simulation: ${test}"
"${DEFAULT_EXECUTION}" ${JOLOKIA_AGENT} ${DEFAULT_JAVA_OPTS} ${JAVA_OPTS} -cp "${GATLING_CLASSPATH}" io.gatling.app.Gatling -s $test

end_time=$(date +%s)000

if [[ -z "${influx_host}" ]]; then
echo "Tests are done"
else
echo "Tests are done"
echo "Generating metrics for comparison table ..."
python compare_build_metrix.py -c $users -t $test_type -d $duration -r $rampup_time -u $url -s $tokenized -st ${start_time} -et ${end_time} -i ${influx_host} -p ${influx_port} -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log
fi
echo "Parsing errors ..."
python logparser.py -c $users -t $test_type -d $duration -r $rampup_time -u $url -s $tokenized -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log
