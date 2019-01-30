#!/bin/bash
export JAVA_OPTS="-Dgatling.http.ahc.pooledConnectionIdleTimeout=150000 -Dgatling.http.ahc.readTimeout=150000 -Dgatling.http.ahc.requestTimeout=150000 -DapiUrl=$environment -Dduration=$duration -Dramp_users=$users -Dramp_duration=$rampup_time -Dgatling.data.writers.0=console -Dgatling.data.writers.1=file -Dcharting.indicators.lowerBound=2000 -Dcharting.indicators.higherBound=3000"
echo $JAVA_OPTS
/opt/gatling/bin/gatling.sh -s $simulation
echo "python logparser.py -c $users -t $test_type -d $duration -r $rampup_time -u $environment -s $tokenized -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log"
python logparser.py -c $users -t $test_type -d $duration -r $rampup_time -u $environment -s $tokenized -f /opt/gatling/results/$(ls /opt/gatling/results/ | grep $tokenized)/simulation.log
