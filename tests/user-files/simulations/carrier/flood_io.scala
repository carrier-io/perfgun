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

  val webProtocol = http
    .baseURL(environment)
    .disableCaching
    .disableFollowRedirect
    .extraInfoExtractor(extraInfo => print_error_processor(extraInfo))

  def flood_io: ScenarioBuilder = {
    scenario("flood_io")
      .exec(Step1GET).exitHereIfFailed
      .exec(Step1POST).exitHereIfFailed
      .exec(Step2GET).exitHereIfFailed
      .exec(Step2POST).exitHereIfFailed
      .exec(Step3GET).exitHereIfFailed
      .exec(Step3POST).exitHereIfFailed
      .exec(Step4GET).exitHereIfFailed
      .exec(Step4POST).exitHereIfFailed
      .exec(dataJSON).exitHereIfFailed
      .exec(Step5GET).exitHereIfFailed
      .exec(Step5POST).exitHereIfFailed
      .exec(FinalStep).exitHereIfFailed
  }

  setUp(flood_io.inject(rampUsers(ramp_users) over(ramp_duration seconds)).protocols(webProtocol))
}
