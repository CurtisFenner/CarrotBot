from scrape import getQuestions
from querytagger import *
from ldatagger import *
from chart import topicsOverTimeChart
import labeler
import os
import random
import sys
import getpass
from piazza_api import Piazza
import _thread as thread
from query_linker import *


################################################################################

with open('configuration.json', 'r') as configurationFile:
    import json
    configuration = json.load(configurationFile)


class CourseFetcher:
    def __init__(self, piazza, configuration):
        self.configuration = configuration
        self.questionsByCourse = {}
        self.taggerByCourse = {}

        self.robots = {}
        self.piazza = piazza
        for course in configuration['courses']:
            for offering in course['offerings']:
                print("Create robot for offering with ID", offering['id'])
                robot = Robot(self.piazza, offering['id'])
                self.robots[offering['id']] = robot

    def runRobots(self):
        for key in self.robots:
            robot = self.robots[key]
            thread.start_new_thread(
                lambda r: r.runForever(), (robot, ))

    def _getCourse(self, name):
        return next(c for c in courses if c['name'] == name)

    def getQuestions(self, courseName):
        if courseName in self.questionsByCourse:
            # TODO: refresh
            return self.questionsByCourse[courseName]

        courses = self.configuration['courses']
        course = self._getCourse(courseName)
        offerings = course['offerings']

        print("Fetching questions for", courseName)
        questions = []
        for offering in offerings:
            questions.extend(getQuestions(offering['id'], self.piazza))
        self.questionsByCourse[courseName] = questions

        print("Course", courseName, "has", len(questions), "questions")
        return questions

    def getLabels(self, courseID):
        return self._getCourse(courseID)['topics']

    def getTagger(self, courseID):
        if courseID in self.taggerByCourse:
            return self.taggerByCourse[courseID]

        questions = self.getQuestions(courseID)
        labels = self.getLabels(courseID)
        print("Training a tagger for", courseID)
        tagger = QueryTagger(questions, labels)
        self.taggerByCourse[courseID] = tagger
        return tagger


# courseName = sys.argv[1]
courses = configuration["courses"]
# course = next(course for course in courses if course["name"] == courseName)
# offerings = course["offerings"]
# labels = course["topics"]

# print("Loaded course `" + courseName + "` with " +
#      str(len(offerings)) + " offering(s)")
# questions = []
# for offering in offerings:
#    print("Offering ID:", offering["id"])
#    questions.extend(getQuestions(offering["id"]))

# our_labels = labeler.loadLabels(COURSE1)
# our_labels.update(labeler.loadLabels(COURSE2))

# Show an accuracy report comparing manual labels to automatic labels
# printAccuracyReport("Ensemble", taggers["query"], questions, our_labels)


email = input('Please enter your email: ')
password = getpass.getpass()

print("Logging in...")
piazza = Piazza()
piazza.user_login(email=email, password=password)

print("Setting up...")
fetcher = CourseFetcher(piazza, configuration)
fetcher.runRobots()

print("Starting HTTP server...")
import server
server.startServer(8080, fetcher)
