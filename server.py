import http.server
import time
import _thread as thread
import json
import re
import urllib.parse as up
from collections import defaultdict

from chart import topicsOverTimeChart
from chart import viewsOverTime
from chart import positivityOverTimeChart


class AnalyticsServer(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if re.match(r"^/*robot.html/*", self.path):
            contentsBin = self.rfile.read(int(self.headers['Content-Length']))
            contents = contentsBin.decode('utf-8')

            # Parse
            d = up.parse_qs(contents)
            print(json.dumps(d))

            if "course" in d and "offering" in d and "set" in d:
                if len(d["offering"]) == 1 and len(d["set"]) == 1:
                    offeringID = d["offering"][0]
                    setValue = d["set"][0]

                    if offeringID in self.server.fetcher.robots:
                        robot = self.server.fetcher.robots[offeringID]
                        if setValue == "true":
                            robot.activated = True
                        else:
                            robot.activated = False

            print("```" + contents + "```")
            self.send_response(303)
            self.send_header('Location', '/robot.html')
            self.end_headers()
            self.wfile.write(
                bytes("go back <a href=/robot.html>to robot activation page</a>\n", 'utf-8'))
            return

    def do_GET(self):
        if self.path == "/robots.json":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            status = {}
            for i in self.server.fetcher.robots:
                status[i] = self.server.fetcher.robots[i].activated

            with open('configuration.json', 'rb') as f:
                self.wfile.write(json.dumps(status).encode('utf-8'))
            return
        elif self.path == "/configuration.json":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            with open('configuration.json', 'rb') as f:
                self.wfile.write(f.read())
            return
        if re.match(r"^/(\?.*)?$", self.path):

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            with open("static/home.html", "rb") as f:
                self.wfile.write(f.read())
            return
        elif re.match(r"^/*robot.html/*$", self.path):

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            with open("static/robot.html", "rb") as f:
                self.wfile.write(f.read())
            return
        elif re.match(r"^/*style.css/*$", self.path):

            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()

            with open("static/style.css", 'rb') as f:
                self.wfile.write(f.read())

        histogramQ = re.match(
            r"^/*([^/]+)/(([^/]+)/+)?histogram.json$",
            self.path
        )

        viewsQ = re.match(
            r"^/*([^/]+)/(([^/]+)/+)?views.json$",
            self.path
        )

        sentimentQ = re.match(
            r"^/*([^/]+)/(([^/]+)/+)?sentiment.json$",
            self.path
        )

        if histogramQ:
            courseID = histogramQ.group(1)
            offering = histogramQ.group(3) or ""

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            questions = self.server.fetcher.getQuestions(courseID)
            if offering != "":
                questions = [q for q in questions if q.courseID == offering]

            tagger = self.server.fetcher.getTagger(courseID)
            x = topicsOverTimeChart(questions, tagger)

            self.wfile.write(bytes(json.dumps(x), 'utf-8'))
        elif viewsQ:
            courseID = viewsQ.group(1)
            offering = viewsQ.group(3) or ""

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            questions = self.server.fetcher.getQuestions(courseID)
            if offering != "":
                questions = [q for q in questions if q.courseID == offering]

            x = viewsOverTime(questions)
            self.wfile.write(bytes(json.dumps(x), 'utf-8'))
        elif sentimentQ:
            courseID = sentimentQ.group(1)
            offering = sentimentQ.group(3) or ""

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            questions = self.server.fetcher.getQuestions(courseID)
            if offering != "":
                questions = [q for q in questions if q.courseID == offering]

            x = positivityOverTimeChart(questions)
            self.wfile.write(bytes(json.dumps(x), 'utf-8'))


def startServer(port, fetcher):
    address = ("localhost", port)
    s = http.server.HTTPServer(address, AnalyticsServer)
    s.fetcher = fetcher

    thread.start_new_thread(lambda x: s.serve_forever(), (1, ))
    print("HTTP server started on", address)

    while True:
        time.sleep(1)
