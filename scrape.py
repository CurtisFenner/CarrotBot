from piazza_api import Piazza
from piazza_api.exceptions import AuthenticationError
from piazza_api.exceptions import RequestError
import json
from bs4 import BeautifulSoup
import re
import os
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer


def toWords(content):
    return [x for x in re.split('[^a-zA-Z0-9]+', content.lower()) if x]


atire_puurula_stopwords = set(line.strip()
                              for line in open('atire_puurula.txt'))


def stem(word, stemmer=SnowballStemmer("english")):
    return " ".join([stemmer.stem(w) for w in word.split(" ")])


# Include stems of all stopwords
atire_puurula_stopwords = atire_puurula_stopwords | \
    set(stem(w) for w in atire_puurula_stopwords)


class QuestionPost:
    def __init__(self, title, body, answer, time):
        self.title = title
        soup = BeautifulSoup(body, "html.parser")
        self.content = soup.get_text()
        soup = BeautifulSoup(answer, "html.parser")
        self.answer = soup.get_text()
        self.time = time
        self.tags = []

    def words(self, include_ans=False):
        words = toWords(self.title) + toWords(self.content)
        if include_ans:
            words += toWords(self.answer)
        return words

    def simpleString(self, include_ans=False):
        words = word_tokenize(" ".join(self.words(include_ans)))
        stops = set(stopwords.words('english'))
        out = []

        for w in words:
            if (w not in stops
                    and not any(c.isdigit() for c in w)):
                out.append(stem(w))
        out += self.tags  # Include tags(?)
        return " ".join(out)


import getpass

_password = "----"


def filterObject(obj):
    #print(type(obj), type(obj) is dict, type(obj) is list)
    ignore = {
        "uid": True,
        "anon": True,
        "bookmarked": True,
        "bucket_name": True,
        "my_favorite": True,
        "name": True,
        "photo": True,
        "facebook_id": True,
    }
    if type(obj) is dict:
        out = {}
        for k in obj:
            if k not in ignore:
                out[k] = filterObject(obj[k])
        return out
    if type(obj) is list:
        return [filterObject(x) for x in obj]
    return obj


def scrapePosts(courseID, sofar, piazza):
    # Connect to Piazza

    seenIDs = [p["id"] for p in sofar]

    sequence = [p for p in sofar]

    if piazza == None:
        return sequence

    count = 0
    try:
        courseNetwork = piazza.network(courseID)
        for post in courseNetwork.iter_all_posts(limit=5000):
            if post["id"] in seenIDs:
                # Pinned posts come first in the feed, so they are only
                # chronological AFTER all of the pinned posts
                if "pin" not in post["tags"]:
                    break
            else:
                # Filter post
                filtered = filterObject(post)
                sequence.append(filtered)
                count += 1
                print("Adding", count, "posts to cache...")
    except RequestError:
        print("User", "???", "could not access course", courseID)
    return sequence


def getPosts(courseID, piazza=None):
    cache = courseID + ".json"
    sofar = []
    if os.path.exists(cache):
        with open(cache, "r") as infile:
            sofar = json.load(infile)

    # No cache exists; scrape
    posts = scrapePosts(courseID, sofar, piazza)

    print("\nWriting", len(posts), "posts to cache file")
    print("/!\\ DO NOT INTERUPT! INTERUPTING WILL CORRUPT CACHE! /!\\")
    with open(cache, "w") as outfile:
        json.dump(posts, fp=outfile)
    print("Written.\n")
    return posts


def processQuestions(posts, courseID):
    questions = []
    for post in posts:
        t = post["type"]
        if t == "question":

            # Get instructor answer
            i_answer = ""
            for i in post["children"]:
                if i["type"] == "i_answer":
                    i_answer = sorted(
                        i["history"], key=lambda x: x["created"])[-1]["content"]

            history = sorted(post["history"], key=lambda p: p["created"])
            mostRecent = history[-1]
            question = QuestionPost(
                title=mostRecent["subject"],
                body=mostRecent["content"],
                answer=i_answer,
                time=mostRecent["created"]
            )
            questions.append(question)
            question.id = post["id"]
            question.number = int(post["nr"])
            question.tags = post["tags"]
            question.courseID = courseID
            question.views = post["unique_views"]
        else:
            pass  # print("Unknown post type `" + t + "`")

    return sorted(questions, key=lambda q: q.time)


def getQuestions(courseID, piazza=None):
    out = processQuestions(getPosts(courseID, piazza), courseID)
    print("getQuestions returning", len(out), "questions for", courseID)
    return out
