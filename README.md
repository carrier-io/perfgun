# perfgun release-1.0
*Carrier customized Gatling container*

### Quick and easy start
These simple steps will run Gatling test against your application.

##### 1. Install docker

##### 2. Start container and pass the necessary config options to container and mount test folder:
`your_local_path_to_tests` - path on your local filesystem where you store gatling tests

`simulation_name` - name of the gatling simulation (with package name if exist) that will be run

`your_local_path_to_config/config.yaml` - config.yaml file with InfluxDB, Jira and Report Portal parameters (described below)

For example:

``` 
docker run --rm -t -u 0:0 \
       -v <your_local_path_to_tests>:/opt/gatling/user-files/ \
       -v <your_local_path_to_config/config.yaml>:/tmp/ \
       -e test=<simulation_name> \
       -e "GATLING_TEST_PARAMS=-DapiUrl=<url> -Dduration=60 ..." \  #optional
       getcarrier/perfgun:latest
```
If your test requires **additional parameters**, such as user count, duration, and so on, they can be passed to GATLING_TEST_PARAMS with the -D option.

To run [demo test](https://github.com/carrier-io/perfgun/blob/master/tests/user-files/simulations/carrier/flood_io.scala) you can use this command:

```
docker run -t -u 0:0 --rm \
       -e test=carrier.Flood \
       -e "GATLING_TEST_PARAMS=-DapiUrl=https://challengers.flood.io -Dduration=10 -Dramp_users=1 -Dramp_duration=1" \
       getcarrier/perfgun:latest
```

### Configuration

Reporting can be configured using [config.yaml](https://github.com/carrier-io/perfgun/blob/master/config.yaml) file.

You have to uncomment the necessary configuration section and pass parameters to use it in your test

**config.yaml** file example:
```
# Reporting configuration section (all report types are optional)
#reportportal:                                        # ReportPortal.io specific section
#  rp_host: https://rp.com                            # url to ReportPortal.io deployment
#  rp_token: XXXXXXXXXXXXX                            # ReportPortal authentication token
#  rp_project_name: XXXXXX                            # Name of a Project in ReportPortal to send results to
#  rp_launch_name: XXXXXX                             # Name of a launch in ReportPortal to send results to
#jira:
#  url: https://jira.com                              # Url to Jira
#  username: some.dude                                # User to create tickets
#  password: password                                 # password to user in Jira
#  jira_project: XYZC                                 # Jira project ID
#  assignee: some.dude                                # Jira id of default assignee
#  issue_type: Bug                                    # Jira issue type (Default: Bug)
#  labels: Performance, perfgun                       # Comaseparated list of lables for ticket
#  watchers: another.dude                             # Comaseparated list of Jira IDs for watchers
#  jira_epic_key: XYZC-123                            # Jira epic key (or id)
#influx:
#  host: carrier_influx                               # Influx host DNS or IP
#  port: 8086                                         # Influx port (Default: 8086)
#  graphite_port: 2003                                # Graphite port (Default: 2003)
#  gatling_db: gatling                                # Database name for gatling test results (Default: gatling)
#  comparison_db: comparison                          # Database name for comparison builds (Default: comparison)
```
