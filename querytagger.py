from scrape import QuestionPost
import re


class QueryTopic:
    def __init__(self, words):
        q = QuestionPost(" ".join(words), "", "", "")
        s = q.simpleString()
        self._words = [x for x in re.split('[^a-zA-Z0-9]+', s) if x]

    def summary(self):
        return "(" + " or ".join(self._words) + ")"

    def matches(self, document):
        for i in range(len(self._words)):
            if self._words[i] in document:
                return True
        return False


class QueryTagger:
    def __init__(self, questions, topics):
        self.topics = topics

        import numpy
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.ensemble import RandomForestClassifier, VotingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier

        documents = numpy.asarray([question.simpleString()
                                   for question in questions])

        self.vectorizer = TfidfVectorizer()
        countMatrix = self.vectorizer.fit_transform(documents)
        self.classifiers = []
        for topic in topics:
            matches = [QueryTopic(topic).matches(document)
                       for document in documents]

            rf = RandomForestClassifier(
                max_depth=10, n_estimators=10, random_state=0)
            lr = LogisticRegression()
            ensemble = [
                # ('1', rf),
                ('2', lr)
            ]

            classifier = VotingClassifier(estimators=ensemble, voting='soft')
            classifier.fit(countMatrix, matches)
            self.classifiers.append(classifier)

    def listTopics(self):
        return self.topics

    def getTopics(self, question):
        document = question.simpleString()
        x = self.vectorizer.transform([document])
        out = []
        for i, classifier in enumerate(self.classifiers):
            prediction = classifier.predict_proba(x)
            out.append((prediction[0][1], self.topics[i]))
        return out

    def getTopicsMany(self, questions):
        documents = [q.simpleString() for q in questions]
        x = self.vectorizer.transform(documents)
        out = [[] for q in questions]
        for i, classifier in enumerate(self.classifiers):
            prediction = classifier.predict_proba(x)
            for q, _ in enumerate(questions):
                p = prediction[q][1]
                t = self.topics[i]
                out[q].append((p, t))
        return out
