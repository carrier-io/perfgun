# Introduction
*Carrier customized Gatling container*

### Docker tags and versioning

getcarrier/perfgun:1.0 - Carrier Perfgun release version 1.0
    
getcarrier/perfgun:latest - bleeding edge, not recommended for production

### Quick and easy start
These simple steps will run Gatling test against your application.

##### 1. Install docker

##### 2. Start container and pass the necessary config options to container and mount test folder:

Example docker invocation:

``` 
docker run --rm -t -u 0:0 \
       -v <your_local_path_to_tests>:/opt/gatling/user-files/ \ 
       -v <your_local_path_to_config/config.yaml>:/tmp/ \ #optional
       -v <your_local_path_ to_reports>:/opt/gatling/results/ \   #optional
       -e test=<simulation_name> \
       -e "GATLING_TEST_PARAMS=-DapiUrl=<url> -Dduration=60 ..." \  #optional
       getcarrier/perfgun:1.0
```

`your_local_path_to_tests` - path on your local filesystem where you store gatling tests

`simulation_name` - name of the gatling simulation (with package name if exist) that will be run

`your_local_path_to_reports` - path on your local filesystem where you want to store reports from this run

`your_local_path_to_config/config.yaml` - config.yaml file with InfluxDB, Loki, Jira and Report Portal parameters (described below)

If your test requires **additional parameters**, such as user count, duration, and so on, they can be passed to GATLING_TEST_PARAMS with the -D option.

To run [demo test](https://github.com/carrier-io/perfgun/blob/master/tests/user-files/simulations/carrier/flood_io.scala) you can use this command:

```
docker run -t -u 0:0 --rm \
       -e test=carrier.Flood \
       -e "GATLING_TEST_PARAMS=-DapiUrl=https://challengers.flood.io -Dduration=10 -Dramp_users=1 -Dramp_duration=1" \
       getcarrier/perfgun:1.0
```

##### 3. Open test report
Report is located in your `your_local_path_to_reports` folder

### Configuration

Error reporting can be configured using config.yaml file.

You can send aggregated errors to Report Portal or Jira. You can also send error info to Loki.

To do this, you need to uncomment the necessary configuration section and pass parameters.

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
#loki:
#  host: http://loki                                  # Loki host DNS or IP
#  port: 3100                                         # Loki port

```

### Jenkins pipeline

Carrier Perfgun can be started inside Jenkins CI/CD pipeline.

Here is an example pipeline that will run demo test.

```
def get_influx_host(String env_var) {
    def match = env_var =~ 'http://(.+)/jenkins'
    return match[0][1]
}

node {
    stage("configure"){
        deleteDir()
        sh 'mkdir reports'
        sh '''echo """influx:
  host: '''+get_influx_host(env.JENKINS_URL)+'''
  port: 8086
  graphite_port: 2003
""" > config.yaml'''
    }
    stage('execute tests') {
        def dockerParamsString = ""
        def params = [
            "--entrypoint=''",
            "-e test=\"carrier.Flood\"",
            "-e GATLING_TEST_PARAMS=\"-DapiUrl=https://challengers.flood.io -Dduration=10 -Dramp_users=1 -Dramp_duration=1\""
        ]
        for (param in params) {
            dockerParamsString += " ${param}"
        }
        docker.image("getcarrier/perfgun:1.0").inside(dockerParamsString) {
            sh "cp ${WORKSPACE}/config.yaml /tmp/config.yaml"
            sh "executor.sh"
            sh "cp -R /opt/gatling/results/* ${WORKSPACE}/reports/"
        }
    }
    stage("publish results"){
        publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'results/*/', reportFiles: 'index.html', reportName: 'Gatling Report', reportTitles: ''])
    }
}
```

In order to run your tests you need to copy your tests or clone your repository with the tests in the Jenkins workspace.

Then, inside the docker.image() block, add the following command:

```
sh "cp -r ${WORKSPACE}/<path_to_user-files_folder> /opt/gatling"
```

`<path_to_user-files_folder` - path in Jenkins workspace where stored Gatling simulation