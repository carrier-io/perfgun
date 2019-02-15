package carrier.utilities

import java.net._
import java.io._

import java.net.URLDecoder

import io.gatling.http.request.ExtraInfo
import io.gatling.core.Predef._
import io.gatling.core.structure.ChainBuilder
import io.gatling.http.request.builder.HttpRequestBuilder


object common_functions {

  def print_error_processor(extraInfo: ExtraInfo) = {
    var body_buffer: String = ""
    var errorcode_buffer: String = ""
    var status_code_buffer: String = ""
    if (extraInfo.status != io.gatling.commons.stats.Status("OK")) {
      status_code_buffer = extraInfo.response.statusCode.fold("")(_.toString)
      body_buffer = extraInfo.response.body.string
      errorcode_buffer = ""
      if (body_buffer.indexOf("alert") > -1) {
        body_buffer = body_buffer.drop(body_buffer.indexOf("alert"))
        body_buffer = body_buffer.take(body_buffer.indexOf("\n"))
      } else if (extraInfo.response.body.string.indexOf("<body") > -1) {
        body_buffer = body_buffer.drop(body_buffer.indexOf("<body"))
        if (body_buffer.indexOf("</body") > -1) {
          body_buffer = body_buffer.take(body_buffer.indexOf("</body"))
        }
      }
      body_buffer = ", Response: " + body_buffer
      if (!extraInfo.response.statusCode.contains(503) && !extraInfo.response.statusCode.contains(504)) {
        if (body_buffer.indexOf("errorcode") > -1) {
          errorcode_buffer = body_buffer.drop(body_buffer.indexOf("errorcode") + 12)
          errorcode_buffer = URLDecoder.decode(errorcode_buffer.take(6), "utf-8")
        }
        if (body_buffer.indexOf("\"code\"") > -1) {
          errorcode_buffer = body_buffer.drop(body_buffer.indexOf("\"code\"") + 7)
          errorcode_buffer = errorcode_buffer.take(errorcode_buffer.indexOf(","))
        }
        if (body_buffer.indexOf("<td>Error: ") > -1) {
          errorcode_buffer = body_buffer.drop(body_buffer.indexOf("<td>Error: ") + 11)
          errorcode_buffer = errorcode_buffer.take(body_buffer.indexOf("</td>"))
        }
        if (body_buffer.indexOf("Error Code: ") > -1) {
          errorcode_buffer = body_buffer.drop(body_buffer.indexOf("Error Code: ") + 12)
          errorcode_buffer = errorcode_buffer.take(body_buffer.indexOf("</td>"))
        }
        if (body_buffer.indexOf("\"Code\"") > -1) {
          errorcode_buffer = body_buffer.drop(body_buffer.indexOf("\"Code\":") + 7)
          errorcode_buffer = errorcode_buffer.take(errorcode_buffer.indexOf(","))
        }
        println("Request URL: " + extraInfo.request.getUrl + "\n")
        println(body_buffer + "\n")
        println("HTTP Code: " + status_code_buffer + "\n")
        if (errorcode_buffer != "") {
          println("Error Code: " + errorcode_buffer + "\n")
          println("Request: " + extraInfo.request + "\n")
          body_buffer = body_buffer + " Error Code: " + errorcode_buffer
          status_code_buffer = errorcode_buffer
        }
      }
      List("Request: " + extraInfo.request + ", HTTP Code: " + status_code_buffer + body_buffer)
    }
    else {
      status_code_buffer = extraInfo.response.statusCode.fold("")(_.toString)
      List("Request: " + extraInfo.request + ", HTTP Code: " + status_code_buffer + ", ")
    }
  }

}


