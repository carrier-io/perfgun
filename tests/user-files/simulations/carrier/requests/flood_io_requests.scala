package carrier.requests

import io.gatling.core.Predef._
import io.gatling.http.Predef._

object requests {

  val headers_5 = Map(
    "Accept-Encoding" -> "gzip, deflate",
    "Pragma" -> "no-cache",
    "Host" -> "challengers.flood.io",
    "Origin" -> "https://challengers.flood.io",
    "Accept" -> "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "X-Requested-With" -> "XMLHttpRequest",
    "Upgrade-Insecure-Requests" -> "1")

  val dataJSON = exec(http("Step5_GET_Code")
    .get("/code")
    .check(jsonPath("$.code").saveAs("dataJSON")))

  val Step1GET = exec(http("Step1_GET")
    .get("/")
    .headers(headers_5)
    .check(status.is(200))
    .check(regex("authenticity_token.*?value=\"(.*?)\"").find.saveAs("token"))
    .check(regex("step_id.+?value=\"(.+?)\"").find.saveAs("challenger"))
    .check(regex("step_number\".*?value=\"(.*?)\"").find.saveAs("stepNumber")))
    .pause(1)

  val Step1POST = exec(http("Step1_POST")
    .post("/start")
    .headers(headers_5)
    .formParam("utf8", "✓")
    .formParam("authenticity_token", "${token}")
    .formParam("challenger[step_id]", "${challenger}")
    .formParam("challenger[step_number]", "${stepNumber}")
    .formParam("commit", "Start"))
    .pause(1)

  val Step2GET = exec(http("Step2_GET")
    .get("/step/2")
    .headers(headers_5)
    .check(regex("step_id.+?value=\"(.+?)\"").find.saveAs("challenger2"))
    .check(regex("step_number\".*?value=\"(.*?)\"").find.saveAs("stepNumber2")))
    .pause(1)

  val Step2POST =
      exec(http("Step2_POST")
        .post("/start")
        .headers(headers_5)
        .formParam("utf8", "✓")
        .formParam("authenticity_token", "${token}")
        .formParam("challenger[step_id]", "${challenger2}")
        .formParam("challenger[step_number]", "${stepNumber2}")
        .formParam("challenger[age]", "18")
        .formParam("commit", "Next"))
     .pause(1)

  val Step3GET =
      exec(http("Step3_GET")
        .get("/step/3")
        .headers(headers_5)
        .check(regex("step_id.+?value=\"(.+?)\"").find.saveAs("challenger3"))
        .check(regex("step_number\".*?value=\"(.*?)\"").find.saveAs("stepNumber3"))
        .check(regex("challenger_order_selected_.+?\">(.+?)<\\/label>").findAll.saveAs("number"))
        .check(regex("radio\" value=\"(.+?)\"").findAll.saveAs("order_selected")))
      .exec(session => {
        val numbers = session("number").as[List[String]]
        val numInt = numbers.map(_.toString.toInt)
        var buttons = session("order_selected").as[List[String]]
        val map: Map[Int, String] = (numInt zip buttons).toMap
        //for ((k, v) <- map) printf("key: %s, value: %s\n", k, v)
        val max = map.keysIterator.max
        val button = map(max)
        session.set("num", max).set("order", button)
      })
      .pause(1)


  val Step3POST = exec(http("Step3_POST")
    .post("/start")
    .headers(headers_5)
    .formParam("utf8", "✓")
    .formParam("authenticity_token", "${token}")
    .formParam("challenger[step_id]", "${challenger3}")
    .formParam("challenger[step_number]", "${stepNumber3}")
    .formParam("challenger[largest_order]", "${num}")
    .formParam("challenger[order_selected]", "${order}")
    .formParam("commit", "Next"))
    .pause(1)

  val Step4GET = exec(http("Step4_GET")
    .get("/step/4")
    .headers(headers_5)
    .check(regex("step_id.+?value=\"(.+?)\"").find.saveAs("challenger4"))
    .check(regex("step_number\".*?value=\"(.*?)\"").find.saveAs("stepNumber4"))
    .check(regex("challenger_order_.+? name=\"(.+?)\".+?value=\".+?\"").findAll.saveAs("orderName"))
    .check(regex("challenger_order_.+? name=\".+?\".+?value=\"(.+?)\"").find.saveAs("orderValue")))
    .exec(session => {
      val orderName = session("orderName").as[List[String]]
      session
        .set("orderName_1", orderName(0))
        .set("orderName_2", orderName(1))
        .set("orderName_3", orderName(2))
        .set("orderName_4", orderName(3))
        .set("orderName_5", orderName(4))
        .set("orderName_6", orderName(5))
        .set("orderName_7", orderName(6))
        .set("orderName_8", orderName(7))
        .set("orderName_9", orderName(8))
        .set("orderName_10", orderName(9))
    })
    .pause(1)

  val Step4POST = exec(http("Step4_POST")
    .post("/start")
    .headers(headers_5)
    .formParam("utf8", "✓")
    .formParam("authenticity_token", "${token}")
    .formParam("challenger[step_id]", "${challenger4}")
    .formParam("challenger[step_number]", "${stepNumber4}")
    .formParam("${orderName_1}", "${orderValue}")
    .formParam("${orderName_2}", "${orderValue}")
    .formParam("${orderName_3}", "${orderValue}")
    .formParam("${orderName_4}", "${orderValue}")
    .formParam("${orderName_5}", "${orderValue}")
    .formParam("${orderName_6}", "${orderValue}")
    .formParam("${orderName_7}", "${orderValue}")
    .formParam("${orderName_8}", "${orderValue}")
    .formParam("${orderName_9}", "${orderValue}")
    .formParam("${orderName_10}", "${orderValue}")
    .formParam("commit", "Next"))

  val Step5GET = exec(http("Step5_GET")
    .get("/step/5")
    .headers(headers_5)
    .check(regex("step_id.+?value=\"(.+?)\"").find.saveAs("challenger5"))
    .check(regex("step_number\".*?value=\"(.*?)\"").find.saveAs("stepNumber5")))

  val Step5POST = exec(http("Step5_POST")
    .post("/start")
    .headers(headers_5)
    .formParam("utf8", "✓")
    .formParam("authenticity_token", "${token}")
    .formParam("challenger[step_id]", "${challenger5}")
    .formParam("challenger[step_number]", "${stepNumber5}")
    .formParam("challenger[one_time_token]", "${dataJSON}")
    .formParam("commit", "Next"))

  val FinalStep = exec(http("Final_Step")
    .get("/done")
    .headers(headers_5)
    .check(regex("You're Done!")))

  val failedFinalStep = exec(http("Final_Step")
    .get("/done")
    .headers(headers_5)
    .queryParam("milestone", "1")
    .queryParam("state", "open")
    .check(regex("You're Done!!!")))
}
