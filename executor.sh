#!/bin/bash
export JAVA_OPTS="-Dgatling.http.ahc.pooledConnectionIdleTimeout=150000 -Dgatling.http.ahc.readTimeout=150000 -Dgatling.http.ahc.requestTimeout=150000 -DapiUrl=$environment -Dduration=$duration -Dramp_users=$users -Dramp_duration=$rampup_time -Dgatling.data.writers.0=console -Dgatling.data.writers.1=file -Dgatling.data.writers.2=graphite -Dcharting.indicators.lowerBound=2000 -Dcharting.indicators.higherBound=3000"
echo $JAVA_OPTS

start_time=$(date +%s)000
/opt/gatling/bin/gatling.sh -s $simulation
end_time=$(date +%s)000

echo "python compare_build_metrix.py -c $users -t $test_type -d $duration -r $rampup_time -u $environment -s $tokenized -st ${start_time} -et ${end_time} -i ${influx_host} -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log"
python compare_build_metrix.py -c $users -t $test_type -d $duration -r $rampup_time -u $environment -s $tokenized -st ${start_time} -et ${end_time} -i ${influx_host} -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log

echo "python logparser.py -c $users -t $test_type -d $duration -r $rampup_time -u $environment -s $tokenized -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log"
python logparser.py -c $users -t $test_type -d $duration -r $rampup_time -u $environment -s $tokenized -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log
