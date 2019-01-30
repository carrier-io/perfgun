package carrier.utilities

import java.net._
import java.io._

import java.util.concurrent.ConcurrentLinkedDeque
import java.net.URLDecoder
import java.security.cert.X509Certificate
import java.security.{DigestInputStream, MessageDigest, SecureRandom}

import io.gatling.http.request.ExtraInfo
import io.gatling.core.Predef._
import io.gatling.core.structure.ChainBuilder
import io.gatling.http.request.builder.HttpRequestBuilder
import javax.net.ssl.{HttpsURLConnection, SSLContext, TrustManager, X509TrustManager}


object common_functions {

  val createGraphiteClient = {
    if (System.getProperty("gatling.data.graphite.host") != null) {
      val s = new Socket(InetAddress.getByName(System.getProperty("gatling.data.graphite.host")), System.getProperty("gatling.data.graphite.port").toInt)
      new PrintStream(s.getOutputStream())
    }
  }

  val random = new util.Random

  val queue = new ConcurrentLinkedDeque[Map[String, Any]]

  def offer(attributes: String*): ChainBuilder = exec({ session =>
    var map = scala.collection.mutable.Map[String, String]()
    attributes.foreach(x => {
      map += (x -> session(x).as[String])
    })
    if (!queue.contains(map)) {
      queue.offer(map.toMap)
    }
    session
  })

  def withPolledRecord(chain: ChainBuilder): ChainBuilder = {
    asLongAs("${emptyQueueFlag.isUndefined()}")({
      exec(session => {
        queue.poll() match {
          case null => session.set("emptyQueueFlag", true)
          case record => session.setAll(record)
        }
      }).doIf(!_.contains("emptyQueueFlag")) {
        exec(chain)
      }
    })
  }

  def cleaningLoop(seqName: String, idName: String, chain: HttpRequestBuilder): ChainBuilder = {
    doIf(_.contains(seqName)) {
      foreach(session => session.get(seqName).as[Seq[String]], idName) {
        exec(
          chain.silent
        )
      }
    }
  }

  def getRandomWord(length: Int): String = {
    scala.util.Random.alphanumeric.take(length).mkString
  }

  def getRandom(low: Int, high: Int): Int = {
    random.nextInt(high - low) + low
  }

  def getBooleanString: String = {
    if (random.nextInt(100) > 50) "true" else "false"
  }

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

  def buildRow(session: Session): String = {
    val filtered = new StringBuilder
    filtered ++= session.get("count").as[Int].toString.concat(",")
    filtered ++= session.get("responseCount").as[Int].toString
    //add any session params above
    val result = filtered.toString()
    result
  }

  def createLogFileForEachThread(): ChainBuilder = {
    val filePath = "../tests/user-files/data/results/"

    doIf(!_.contains("print_writer")) {
      exec(session => {
        val output = new FileOutputStream(filePath + "relevancy_count_" + session.userId.toString + ".csv", false)
        val pw = new java.io.PrintWriter(output, true)
        pw.println("RequestCount,ResponseCount")
        session.set("print_writer", pw)
      })
    }
    //then in exec session:
    /*
    val dataRow = buildRow(session)
    session.get("print_writer").as[PrintWriter].println(dataRow)
    */
  }

  def ignoreSSLVerification(): Any = {
    val dummyTrustManager = Array[TrustManager](new X509TrustManager() {
      def getAcceptedIssuers: Array[X509Certificate] = null

      def checkClientTrusted(certs: Array[X509Certificate], authType: String): Unit = {
      }

      def checkServerTrusted(certs: Array[X509Certificate], authType: String): Unit = {
      }
    })

    val sc = SSLContext.getInstance("SSL")
    sc.init(null, dummyTrustManager, new SecureRandom)
    HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory)
  }

  def fileDownloader(file_url: String, filename: String, session_id: String): Any = {

    ignoreSSLVerification()

    val url = new URL(file_url)
    val path = "/opt/gatling/user-files/bodies/dmi/" + filename

    try {
      val connection = url.openConnection().asInstanceOf[HttpURLConnection]
      connection.setRequestMethod("GET")
      connection.setRequestProperty("controldata", """{"UserCredentialData":{"SessionId":"""" + session_id +"""","AccountId":"9GTV000100","UserId":"E000103763","Namespace":"16"},"RoutingData":{"ContentServerAddress":0,"TransportType":"RTS"},"UserCommerceData":{},"PlatformAdminData":{"TransactionTimeout":60}}""")
      connection.setConnectTimeout(5000)
      connection.setReadTimeout(10000)
      connection.connect()
      if (connection.getResponseCode <= 201) {
        val in: InputStream = connection.getInputStream
        val fileToDownloadAs = new java.io.File(path)
        val out: OutputStream = new BufferedOutputStream(new FileOutputStream(fileToDownloadAs))
        val byteArray = Stream.continually(in.read).takeWhile(-1 !=).map(_.toByte).toArray
        out.write(byteArray)
        out.close()
        println("downloaded")
        connection.disconnect()
      } else {
        val br = new BufferedReader(new InputStreamReader(connection.getErrorStream))
        println(br.readLine())
        connection.disconnect()
      }
    } catch {
      case ex: Throwable => println("Download failed. " + ex.getMessage)
    }
  }

  def getRequest(request_url: String): String = {
    ignoreSSLVerification()

    val url = new URL(request_url)
    var response = ""

    try {
      val connection = url.openConnection().asInstanceOf[HttpURLConnection]
      connection.setRequestMethod("GET")
      connection.setConnectTimeout(5000)
      connection.setReadTimeout(5000)
      connection.connect()
      if (connection.getResponseCode <= 201) {
        val br = new BufferedReader(new InputStreamReader(connection.getInputStream))
        response = br.readLine()
        connection.disconnect()
      } else {
        val br = new BufferedReader(new InputStreamReader(connection.getErrorStream))
        println(br.readLine())
        connection.disconnect()
      }
    }
    catch {
      case ex: Throwable => println("Request exception. " + ex.getMessage)
    }

    response
  }

}


