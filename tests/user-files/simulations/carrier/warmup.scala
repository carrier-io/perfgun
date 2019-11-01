package carrier

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.core.structure.ScenarioBuilder

class WarmUp extends Simulation {

  val webProtocol = http
    .baseUrl("https://www.google.com")
    .disableCaching
    .disableFollowRedirect

  def warmup: ScenarioBuilder = {
    scenario("warmup")
      .exec(http("test").get("/")).exitHereIfFailed
  }

  setUp(warmup.inject(atOnceUsers(1))).protocols(webProtocol)
}