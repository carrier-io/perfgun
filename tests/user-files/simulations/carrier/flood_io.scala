package carrier

import io.gatling.core.Predef._
import io.gatling.core.structure.ScenarioBuilder
import io.gatling.http.Predef._
import carrier.utilities.common_functions.print_error_processor
import carrier.requests.requests._

class Flood extends Simulation {

  val environment = System.getProperty("apiUrl")
  val ramp_users = Integer.getInteger("ramp_users")
  val ramp_duration = Integer.getInteger("ramp_duration")
  val duration = Integer.getInteger("duration")

  val webProtocol = http
    .baseURL(environment)
    .disableCaching
    .disableFollowRedirect

  def flood_io: ScenarioBuilder = {
    scenario("flood_io")
      .during(duration, exitASAP = true) {
        tryMax(10) {
          exec(Step1GET)
            .exec(Step1POST)
            .exec(Step2GET)
            .exec(Step2POST)
            .exec(Step3GET)
            .exec(Step3POST)
            .exec(Step4GET)
            .exec(Step4POST)
            .exec(dataJSON)
            .exec(Step5GET)
            .exec(Step5POST)
            .randomSwitch(60.0 -> exec(FinalStep),
              40.0 -> exec(failedFinalStep))
        }.exitHereIfFailed
      }
  }

  setUp(flood_io.inject(rampUsers(ramp_users) over(ramp_duration seconds)).protocols(webProtocol))
}
