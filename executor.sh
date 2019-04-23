#!/bin/bash

export tokenized=$(python -c "from os import environ; print(environ['test'].split('.')[1].lower())")
export config=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()); print(y)")
if [[ "${config}" != "None" ]]; then
export influx_host=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print(y.get('host'))")
export influx_port=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print(y.get('port',8086))")
export graphite_port=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print(y.get('graphite_port',2003))")
export gatling_db=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print(y.get('gatling_db', 'gatling'))")
export comparison_db=$(python -c "import yaml; y = yaml.load(open('/tmp/config.yaml').read()).get('influx',{}); print(y.get('comparison_db', 'comparison'))")
export report_portal=$(python -c "import yaml; print (yaml.load(open('/tmp/config.yaml').read()).get('reportportal',{}))")
export jira=$(python -c "import yaml; print(yaml.load(open('/tmp/config.yaml').read()).get('jira',{}))")
export loki=$(python -c "import yaml; print(yaml.load(open('/tmp/config.yaml').read()).get('loki',{}))")
else
export influx_host="None"
export jira="{}"
export report_portal="{}"
fi
if [[ -z "${test_type}" ]]; then
export test_type="test"
fi

if [[ -z "${env}" ]]; then
export env="stag"
fi

if [[ -z "${users}" ]]; then
export users=0
fi

if [[ "${influx_host}" != "None" ]]; then
export influx_piece="-Dgatling.data.graphite.host=${influx_host} -Dgatling.data.graphite.port=${graphite_port} -Dgatling.data.graphite.rootPathPrefix=${test_type}.${env}.${users}"
else
export influx_piece=""
fi

sudo sed -i "s/LOAD_GENERATOR_NAME/${lg_name}_${tokenized}_${lg_id}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/INFLUX_HOST/http:\/\/${influx_host}:${influx_port}/g" /etc/telegraf/telegraf.conf
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
export COMPILER_CLASSPATH="${GATLING_HOME}/lib/zinc/*:${GATLING_CONF}:"
export GATLING_CLASSPATH="${GATLING_HOME}/lib/*:${GATLING_HOME}/user-files:${GATLING_CONF}:"

export JAVA_OPTS="-Dgatling.http.ahc.pooledConnectionIdleTimeout=150000 -Dgatling.http.ahc.readTimeout=150000 -Dgatling.http.ahc.requestTimeout=150000 ${influx_piece} -Dgatling.data.writers.0=console -Dgatling.data.writers.1=file -Dgatling.data.writers.2=graphite -Dcharting.indicators.lowerBound=2000 -Dcharting.indicators.higherBound=3000 ${GATLING_TEST_PARAMS}"

echo $JAVA_OPTS
export COMPILER_OPTS="-Xss100M ${DEFAULT_JAVA_OPTS} ${JAVA_OPTS}"
export COMPILATION_CLASSPATH=`find "${GATLING_HOME}/lib" -maxdepth 1 -name "*.jar" -type f -exec printf :{} ';'`
cd /opt/gatling/bin

start_time=$(date +%s)000
echo "Starting simulation: ${test}"
"$DEFAULT_EXECUTION" $COMPILER_OPTS -cp "$COMPILER_CLASSPATH" io.gatling.compiler.ZincCompiler -ccp "$COMPILATION_CLASSPATH"  2> /dev/null
"$DEFAULT_EXECUTION" $JOLOKIA_AGENT $DEFAULT_JAVA_OPTS $JAVA_OPTS -cp "$GATLING_CLASSPATH" io.gatling.app.Gatling -s $test

end_time=$(date +%s)000

export simulation_folder=$(python -c "from os import environ; print(environ['test'].split('.')[1].lower().replace('_', '-'))")

if [[ "${influx_host}" != "None" ]]; then
echo "Tests are done"
echo "Generating metrics for comparison table ..."
if [[ -z "${build_id}" ]]; then
export _build_id=""
else
export _build_id="-b ${build_id}"
fi
python compare_build_metrix.py -t $test_type -l ${lg_id} ${_build_id} -s $tokenized -st ${start_time} -et ${end_time} -i ${influx_host} -p ${influx_port} -gdb ${gatling_db} -cdb ${comparison_db} -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $simulation_folder)/simulation.log
else
echo "Tests are done"
fi
if [[ "${report_portal}" != "{}" || "${jira}" != "{}" || "${loki}" != "{}" ]]; then
echo "Parsing errors ..."
python logparser.py -t $test_type -s $tokenized -st ${start_time} -et ${end_time} -i ${influx_host} -p ${influx_port} -gdb ${gatling_db} -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $simulation_folder)/simulation.log
fi