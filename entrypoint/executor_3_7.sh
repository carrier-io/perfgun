#!/bin/bash

#RUN INFLUXDB
bash /entrypoint.sh influxd &

export simulation_name=$test_name
export influx_host="None"
export influx_port=8086
export gatling_db="gatling"
export comparison_db="comparison"
export telegraf_db="telegraf"
export influx_user=""
export influx_password=""

if [[ -z "${influxdb_host}" ]]; then
true
else
export influx_host=${influxdb_host}
fi
if [[ -z "${influxdb_port}" ]]; then
true
else
export influx_port=${influxdb_port}
fi
if [[ -z "${influxdb_user}" ]]; then
true
else
export influx_user=${influxdb_user}
fi
if [[ -z "${influxdb_password}" ]]; then
true
else
export influx_password=${influxdb_password}
fi
if [[ -z "${influxdb_database}" ]]; then
true
else
export gatling_db=${influxdb_database}
fi
if [[ -z "${influxdb_comparison}" ]]; then
true
else
export comparison_db=${influxdb_comparison}
fi
if [[ -z "${influxdb_telegraf}" ]]; then
true
else
export telegraf_db=${influxdb_telegraf}
fi
if [[ -z "${test_type}" ]]; then
export test_type="demo"
fi
if [[ -z "${env}" ]]; then
export env="demo"
fi
if [[ -z "${build_id}" ]]; then
export build_id=${simulation_name}"_"${test_type}"_"$RANDOM
fi

export lg_id="Lg_"$RANDOM"_"$RANDOM

if [[ "${loki_host}" ]]; then
/usr/bin/promtail/promtail-linux-amd64 --client.url=${loki_host}:${loki_port}/api/prom/push --client.external-labels=hostname=${lg_id} -config.file=/etc/promtail/docker-config.yaml &
fi

if [[ "${influx_host}" != "None" ]]; then
sudo sed -i "s/BUILD_ID/${build_id}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/LOAD_GENERATOR_NAME/${lg_name}_${simulation_name}_${lg_id}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/INFLUX_HOST/http:\/\/${influx_host}:${influx_port}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/telegraf/${telegraf_db}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/INFLUX_USER/${influx_user}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/INFLUX_PASSWORD/${influx_password}/g" /etc/telegraf/telegraf.conf
sudo sed -i "s/INFLUX_HOST/http:\/\/${influx_host}:${influx_port}/g" /etc/telegraf/telegraf_test_results.conf
sudo sed -i "s/INFLUX_DB/${gatling_db}/g" /etc/telegraf/telegraf_test_results.conf
sudo sed -i "s/INFLUX_USER/${influx_user}/g" /etc/telegraf/telegraf_test_results.conf
sudo sed -i "s/INFLUX_PASSWORD/${influx_password}/g" /etc/telegraf/telegraf_test_results.conf
sudo service telegraf restart
sudo telegraf -config /etc/telegraf/telegraf_test_results.conf &
sudo telegraf -config /etc/telegraf/telegraf_local_results.conf &
fi

if [[ -z "${influx_user}" ]]; then
export _influx_user=""
else
export _influx_user="-iu ${influx_user}"
fi

if [[ -z "${influx_password}" ]]; then
export _influx_password=""
else
export _influx_password="-ip ${influx_password}"
fi

if [[ "${influx_host}" != "None" ]]; then
export _influx_host="-i ${influx_host}"
else
export _influx_host=""
fi

mkdir '/tmp/data_for_post_processing'
export tests_path=/opt/gatling
python /opt/gatling/bin/minio_reader.py
python /opt/gatling/bin/minio_additional_files_reader.py
if [[ "${compile}" != true ]]; then
#python /opt/gatling/bin/minio_args_poster.py -t $test_type -s $simulation_name -b ${build_id} -l ${lg_id} ${_influx_host} -p ${influx_port} -idb ${gatling_db} -icdb ${comparison_db} -en ${env} ${_influx_user} ${_influx_password}
python /opt/gatling/bin/downsampling.py -t $test_type -s $simulation_name -b ${build_id} -l ${lg_id} ${_influx_host} -p ${influx_port} -idb ${gatling_db} -en ${env} ${_influx_user} ${_influx_password} &
fi

if [[ -z "${JVM_ARGS}" ]]; then
  export JVM_ARGS="-Xms1g -Xmx1g"
fi
echo "Using ${JVM_ARGS} as JVM Args"
DEFAULT_EXECUTION="/usr/bin/java"
JOLOKIA_AGENT="-javaagent:/opt/java/jolokia-jvm-1.6.0-agent.jar=config=/opt/jolokia.conf"
DEFAULT_JAVA_OPTS=" -server ${JVM_ARGS} -XX:+UseG1GC -XX:MaxGCPauseMillis=30"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -XX:G1HeapRegionSize=16m -XX:InitiatingHeapOccupancyPercent=75"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -XX:+ParallelRefProcEnabled -XX:+PerfDisableSharedMem -XX:+AggressiveOpts"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -XX:+OptimizeStringConcat -XX:+HeapDumpOnOutOfMemoryError"
DEFAULT_JAVA_OPTS="${DEFAULT_JAVA_OPTS} -Djava.net.preferIPv4Stack=true -Djava.net.preferIPv6Addresses=false "
export GATLING_HOME="/opt/gatling"
export GATLING_CONF="${GATLING_HOME}/conf"
export GATLING_CLASSPATH="${GATLING_HOME}/lib/*:${GATLING_HOME}/user-files:${GATLING_CONF}:"
export COMPILER_CLASSPATH="$GATLING_HOME/lib/*:$GATLING_CONF:"

export JAVA_OPTS="-Dsimulation_name=${simulation_name} -Denv=${env} -Dtest_type=${test_type} -Dbuild_id=${build_id} -Dlg_id=${lg_id} -Dgatling.http.ahc.pooledConnectionIdleTimeout=150000 -Dgatling.http.ahc.readTimeout=150000 -Dgatling.http.ahc.requestTimeout=150000 -Dgatling.data.writers.0=console -Dgatling.data.writers.1=file -Dcharting.indicators.lowerBound=2000 -Dcharting.indicators.higherBound=3000 ${GATLING_TEST_PARAMS}"

echo $JAVA_OPTS
export COMPILER_OPTS="-Xss100M ${DEFAULT_JAVA_OPTS} ${JAVA_OPTS}"
#export COMPILATION_CLASSPATH=`find "${GATLING_HOME}/lib" -maxdepth 1 -name "*.jar" -type f -exec printf :{} ';'`
cd /opt/gatling/bin

echo "Starting simulation: ${test}"
if [[ "${compile_and_run}" == true ]]; then
"$DEFAULT_EXECUTION" $COMPILER_OPTS -cp "$COMPILER_CLASSPATH" io.gatling.compiler.ZincCompiler "$@" 2> /dev/null
"$DEFAULT_EXECUTION" $JOLOKIA_AGENT $DEFAULT_JAVA_OPTS $JAVA_OPTS -cp "$GATLING_CLASSPATH" io.gatling.app.Gatling -s $test
sleep 60s
python post_processor.py -t $test_type -s $simulation_name -b ${build_id} -l ${lg_id} ${_influx_host} -p ${influx_port} -idb ${gatling_db} -icdb ${comparison_db} -en ${env} ${_influx_user} ${_influx_password}
else
if [[ "${compile}" == true ]]; then
"$DEFAULT_EXECUTION" $COMPILER_OPTS -cp "$COMPILER_CLASSPATH" io.gatling.compiler.ZincCompiler "$@" 2> /dev/null
python3 minio_poster.py
else
"$DEFAULT_EXECUTION" $JOLOKIA_AGENT $DEFAULT_JAVA_OPTS $JAVA_OPTS -cp "$GATLING_CLASSPATH" io.gatling.app.Gatling -s $test
sleep 60s
python post_processor.py -t $test_type -s $simulation_name -b ${build_id} -l ${lg_id} ${_influx_host} -p ${influx_port} -idb ${gatling_db} -icdb ${comparison_db} -en ${env} ${_influx_user} ${_influx_password}
fi
fi