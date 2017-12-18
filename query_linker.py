from scrape import *
from bs4 import BeautifulSoup
import datetime
import getpass
import math
import numpy as np
import re
import time


class LDALinker:
    def __init__(self, questions):
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
        self.vectorizer = CountVectorizer()
        documents = [q.simpleString() for q in questions]
        wordCountMatrix = self.vectorizer.fit_transform(documents)
        self.vocabulary = self.vectorizer.get_feature_names()
        self.questions = questions

        self.model = LatentDirichletAllocation(
            n_components=20,
            random_state=100,
            learning_method="batch",
            max_iter=50
        )
        print("Fitting...", wordCountMatrix.shape)
        self.model.fit(wordCountMatrix)
        print("Fitted.")
        self.vectors = []
        for q in questions:
            self.vectors.append(self.getVector(q))

    def getVector(self, question):
        import numpy
        document = question.simpleString()
        matrix = self.vectorizer.transform(numpy.reshape([document], 1, -1))
        vector = self.model.transform(matrix)
        return vector[0]

    def sim(self, a, b):
        import numpy
        # a and b are numpy vectors
        # 1 - H^2
        return numpy.sum(numpy.sqrt(a * b))
        """
        # TODO: replace with 1 - hellinger distance
        return numpy.dot(a, b)
        """

    def getSimilarPosts(self, question):
        """
        RETURNS a list of tuples (similarity, question, vector) sorted by
                decreasing similarity.
                question: a QuestionPost.
                similarity: a double
                vector: a list of doubles
                , the query vector, a vectorizer
        """

        queryVector = self.getVector(question)

        out = []
        for i, question in enumerate(self.questions):
            v = self.vectors[i]  # equiv. to self.getVector(question)
            sim = self.sim(v, queryVector)
            out.append((sim, question, v))

        return out, queryVector.tolist()[0], self.vectorizer


class MpLinker:
    def __init__(self, questions, p=0.2):
        import numpy
        from sklearn.feature_extraction.text import CountVectorizer
        documents = np.asarray(
            [q.simpleString(include_ans=True) for q in questions])
        self.vectorizer = CountVectorizer(
            binary=True, ngram_range=(1, 2), max_df=0.35, min_df=3)

        # Fit the vectorizer to the documents and record the vocabulary
        self.countMatrix = self.vectorizer.fit_transform(documents)
        vocab = []
        for k in self.vectorizer.vocabulary_:
            vocab.append((self.vectorizer.vocabulary_[k], k))
        self.vocabulary = [x[1] for x in sorted(vocab)]

        self.questions = questions
        self.p = p
        presence = numpy.sum(self.countMatrix, axis=0)
        self.Nj = presence.tolist()[0]

    def vSimVec(self, nva, nvb):
        nva1 = nva
        nvb1 = nvb

        presentBothArray = nva1.multiply(nvb1).nonzero()
        presentOneArray = (nva1 != nvb1).nonzero()
        presentBoth = presentBothArray[1].tolist()
        presentOne = presentOneArray[1].tolist()

        # each are numpy.ndarray

        N = len(self.questions)
        terms = 0
        s = 0

        # Loop is unnecessary
        for i in presentOne:
            weight = -math.log(self.Nj[i] / N)
            terms += weight
            r = N
            t = r / N
            s += weight * (t ** self.p)

        for i in presentBoth:
            weight = -math.log(self.Nj[i] / N)
            terms += weight
            r = self.Nj[i]
            t = r / N
            s += weight * (t ** self.p)

        return 1 - (s / terms) ** (1 / self.p)

    def vSim(self, nva, nvb):
        # nva, nvb are csr_matrix
        # mp similarity:
        # https://link.springer.com/chapter/10.1007/978-3-319-28940-3_33

        ans = self.vSimVec(nva, nvb)
        return ans

    def vec(self, q):
        document = np.asarray([q.simpleString(include_ans=False)])
        return self.vectorizer.transform(document)

    def getLosses(self, query, question):
        queryVector = self.vec(query)
        compareVector = self.vec(question)

        plain = self.vSim(queryVector, compareVector)

        presentOne = (queryVector != compareVector).nonzero()[1].tolist()

        N = len(self.questions)
        losses = []
        for t in presentOne:
            word = self.vocabulary[t]
            compareVector[0, t] = queryVector[0, t]
            loss = self.vSim(queryVector, compareVector)
            compareVector[0, t] = 1 - queryVector[0, t]
            weight = -math.log(self.Nj[t] / N)
            losses.append((loss - plain, word, weight))
        return losses

    def getSimilarPosts(self, question):
        queryVector = self.vec(question)
        out = []
        for i, q in enumerate(self.questions):
            v = self.countMatrix[i, :]
            sim = self.vSim(queryVector, v)
            sim = sim * 0.99 + 0.01
            queryTime = parse_rfc3339(question.time)
            delta = queryTime - parse_rfc3339(self.questions[i].time)
            days = delta.total_seconds() / 24 / 60 / 60
            weight = 1  # 0.9 + 0.1 * math.exp(-days / 10)

            out.append({
                "similarity": sim * weight,
                "question": q,
                "vector": v,
            })
        return out, queryVector, self.vectorizer


class QueryLinker:
    def __init__(self, questions):
        from sklearn.feature_extraction.text import TfidfVectorizer

        documents = np.asarray([question.simpleString(include_ans=True)
                                for question in questions])

        self.vectorizer = TfidfVectorizer(
            binary=False, use_idf=True, ngram_range=(1, 2), min_df=3, max_df=0.35)
        self.countMatrix = self.vectorizer.fit_transform(documents).todense()
        self.questions = questions

        vocab = []
        for k in self.vectorizer.vocabulary_:
            vocab.append((self.vectorizer.vocabulary_[k], k))
        self.vocabulary = [x[1] for x in sorted(vocab)]

    def getSimilarPosts(self, question):
        """
        RETURNS a list of records (similarity, question, vector) UNSORTED.
                question: A QuestionPost.
                similarity: a double
                vector: a list of doubles
                , the query vector, a vectorizer
        """

        queryTime = parse_rfc3339(question.time)

        question = np.asarray([question.simpleString(include_ans=False)])
        countQuestion = self.vectorizer.transform(question).todense()

        similarity = (self.countMatrix * countQuestion.T)
        similarity = np.squeeze(np.asarray(similarity))
        # No need to divide by magnitude! countMatrix[i] and countQuestion
        # are already normalized

        # Weigh down older posts
        scores = []
        for i in range(len(similarity)):
            delta = queryTime - parse_rfc3339(self.questions[i].time)
            days = delta.total_seconds() / 24 / 60 / 60
            weight = 0.3 + 0.7 * math.exp(-days / 10)

            scores.append(similarity[i] * weight)

        assert len(similarity) == len(self.questions)

        queryList = countQuestion.tolist()[0]

        out = []
        for i in range(len(similarity)):
            out.append({
                # Score should be used for ranking (includes time)
                "score": scores[i],

                # Similarity should be used for filtering (excludes time)
                "similarity": (scores[i] * 9 + similarity[i]) / 10,

                # The question itself
                "question":  self.questions[i],

                # A vector describing how the question was compared to others
                "vector": self.countMatrix[i].tolist()[0],

                # Ignore this
                "losses": "???",
            })

        return out, queryList, self.vectorizer


def parse_rfc3339(dt):
    # SOURCE: https://stackoverflow.com/questions/1941927/convert-an-rfc-3339-time-to-a-standard-python-timestamp
    broken = re.search(
        r'([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(\.([0-9]+))?(Z|([+-][0-9]{2}):([0-9]{2}))', dt)
    return(datetime.datetime(
        year=int(broken.group(1)),
        month=int(broken.group(2)),
        day=int(broken.group(3)),
        hour=int(broken.group(4)),
        minute=int(broken.group(5)),
        second=int(broken.group(6)),
        microsecond=int(broken.group(8) or "0"),
        tzinfo=datetime.timezone(datetime.timedelta(
            hours=int(broken.group(10) or "0"),
            minutes=int(broken.group(11) or "0")))))


def printComparison(va, vb, vocabulary):
    assert len(va) == len(vb)

    print("mag a:", sum(x * x for x in va))
    print("mag b:", sum(x * x for x in vb))

    s = 0
    for i in range(len(va)):
        a = va[i]
        b = vb[i]
        if a == 0 and b == 0:
            continue

        print("\t\t", vocabulary[i], a, "*", b, "=>", a * b)


class Robot:
    CONFIDENCE = 0.5
    MAX_RESPONSES = 3  # Max number of links to provide

    def __init__(self, piazza, class_code):
        self.class_code = class_code
        self.network = piazza.network(class_code)
        self.user_profile = piazza.get_user_profile()
        self.activated = False

    # returns whether the given post already has an instructor answer
    @staticmethod
    def hasInstructorAnswer(post):
        return any(d for d in post["change_log"] if d["type"] == "i_answer")

    # returns whether the given post already has a Robot answer
    def hasRobotAnswer(self, post):
        for i in post["children"]:
            if i.get("uid", None) == self.user_profile["user_id"]:
                return True
        return False

    def refreshPosts(self):
        self.posts = [p for p in self.network.iter_all_posts(limit=5000)]

    def respondToPosts(self):
        need_answer = [p for p in self.posts if not self.hasInstructorAnswer(p)
                       and not self.hasRobotAnswer(p)]
        need_answer = processQuestions(need_answer, self.class_code)

        has_answer = [p for p in self.posts if self.hasInstructorAnswer(p)
                      or self.hasRobotAnswer(p)]
        has_answer = processQuestions(has_answer, self.class_code)
        if len(need_answer) == 0 or len(has_answer) == 0:
            return

        print("All posts:", [p["nr"] for p in self.posts])
        print("Needed:", [p.number for p in need_answer])
        linker = QueryLinker(has_answer)
        for query in need_answer:
            print("Needs answer:", query.number)
            results, queryVector, _ = linker.getSimilarPosts(query)
            results = sorted(
                results, key=lambda x: x['similarity'], reverse=True)
            # similarity, sim_questions = linker.getSimilarPosts(query)

            # Get 5 most relevent posts
            relevant = []
            for result in results:
                similarity = result['similarity']
                question = result['question']

                print("similarity:", similarity, "vs", self.CONFIDENCE)
                print("score:", result['score'])
                # printComparison(
                #     queryVector, result['vector'], linker.vocabulary)
                # Filter by similarity (which does NOT include time component)
                if similarity < self.CONFIDENCE:
                    continue
                if question.answer == "":
                    continue
                relevant.append(result)

            # If no relevent questions, break
            if len(relevant) == 0:
                continue

            # Rank by score (which includes time component)
            relevant = sorted(relevant, key=lambda x: x["score"], reverse=True)
            relevant = relevant[0:self.MAX_RESPONSES]

            # Post relevant links
            text = "<p>Maybe one of these are relevant: </p>"
            print("Post number ", query.number, " answered")
            for r in relevant:
                link = r["question"]
                print("\t", query.number, "=>", link.number, "with",
                      int(r["similarity"] * 100), "% similarity and ", int(r["score"] * 100), "% score")
                #printComparison(queryVector, vector, linker.vocabulary)
                text += "<p>@" + str(link.number) + \
                    " <b>" + link.title + "</b></p>"

                # Add preview text
                content = link.content
                answer = link.answer
                if len(content) > 200:
                    content = link.content[0:200] + "..."
                elif len(answer) > 200:
                    answer = link.answer[0:200] + "..."
                text += "<p><i>Question: " + content + "</i></p>"
                text += "<p>Instructor Response: " + answer + "</p>"
                text += "<p></p>"

            # text += ",  ".join("@" + str(r.number) for r in relevant)
            self.network.create_followup(query.__dict__, text)

    def runForever(self):
        while True:
            if self.activated:
                self.refreshPosts()
                self.respondToPosts()
            time.sleep(5)
