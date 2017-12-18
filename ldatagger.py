from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from collections import defaultdict

from scrape import QuestionPost
import numpy
import random


class LDATopic:
    def __init__(self, pairs):
        self._pairs = pairs

    def summary(self):
        return "{" + ", ".join(map(lambda x: x[0], sorted(self._pairs, key=lambda x: x[1])[-20:])) + ", ...}"

    def getWords(self):
        return [x[0] for x in sorted(self._pairs, key=lambda x: x[1], reverse=True)]


def relevance(a, b):
    return a.dot(b) / numpy.linalg.norm(a) / numpy.linalg.norm(b)


class LDAQuestionTagger:
    def __init__(self, questions, topicCount, labels):
        """Initializes an LDA tagger with the given corpus of questions.
        `corpus` is a Question list
        """
        self.labels = labels

        self.vectorizer = CountVectorizer()
        documents = [question.simpleString() for question in questions]
        wordCountMatrix = self.vectorizer.fit_transform(documents)
        self.vocabulary = self.vectorizer.get_feature_names()
        wordsums = numpy.asarray(
            numpy.sum(wordCountMatrix, axis=0)).reshape(-1)
        self.wordCountMap = defaultdict(lambda: 0)
        for i in range(len(wordsums)):
            self.wordCountMap[self.vocabulary[i]] += wordsums[i]

        self.model = LatentDirichletAllocation(
            n_components=topicCount,
            random_state=100,
            learning_method="batch",
            max_iter=50
        )
        self.model.fit_transform(wordCountMatrix)

    def _documentToWordCountMatrix(self, document):
        import numpy
        return self.vectorizer.transform(numpy.reshape([document], 1, -1))

    # RETURNS a vector
    def getInternalTopics(self, question):
        import numpy
        document = question.simpleString()
        vector = self._documentToWordCountMatrix(document)
        out = self.model.transform(vector)
        return out[0]

    def listInternalTopics(self):
        topics = []
        for topicID, weights in enumerate(self.model.components_):
            topic = []
            for i in range(len(weights)):
                topic.append((self.vocabulary[i], weights[i]))
            topics.append(LDATopic(topic))
        return topics

    def _randomWord(self):
        total = 0
        for key in self.wordCountMap:
            total += self.wordCountMap[key]

        total *= random.random()
        for key in self.wordCountMap:
            total -= self.wordCountMap[key]
            if total <= 0:
                return key

    # RETURNS weighted labels (from self.labels)
    def getTopics(self, question):
        numpy.set_printoptions(
            formatter={'float': lambda x: "{0:0.2f}".format(x)})

        internal = numpy.array(self.getInternalTopics(question))
        fakes = [QuestionPost(" " .join([self._randomWord() for _ in range(20 * len(label))] + label * 80), "", "")
                 for label in self.labels]

        columns = [numpy.array(self.getInternalTopics(fake)) for fake in fakes]

        out = []
        # print()
        #print(". " * 40)
        # print(question.title)
        # print(question.content)
        #print("vector:", internal)
        for i in range(len(self.labels)):
            #print("l[" + str(i) + "]: ", self.labels[i])
            #print("c[" + str(i) + "]: ", columns[i])
            weight = relevance(columns[i], internal)
            #print("\trelevance:", weight)
            # print()
            out.append((weight, self.labels[i]))

        #print("out:", out)
        # print()
        # print()
        return out
        """
        matrix = numpy.column_stack(columns)
        print()
        print()
        print("#", question.title)
        print("matrix:", matrix)
        print("vector:", internal)
        print()
        print()

        # Solve linear equation
        solution = numpy.linalg.lstsq(matrix, internal)[0]
        solution.shape = (len(solution), 1)
        print("solution:", solution)
        print("matrix.shape", matrix.shape)
        print("solution.shape", solution.shape)
        print("vector.shape", internal.shape)
        print("back:", numpy.dot(matrix, solution))

        out = []
        for i in range(len(self.labels)):
            out.append((solution[i], self.labels[i]))
        return out
        """


"""
    num_matches = 0
    for num, i in enumerate(tags):
        topic = tagger.listTopics()[i].getWords()
        best = 1000
        for j in eecs370_labels:
            local_best = 1000
            for k in j:
                if k in topic and topic.index(k) < local_best:
                    local_label = j
                    local_best = topic.index(k)
            if local_best < best:
                label = local_label
                best = local_best
        print("Sam Label: ", sam_labels[num])
        print(key + " Label: ", label)
        if [x for x in label if x in sam_labels[num]]:
            num_matches += 1
            print("Match")
        else:
            print("No Match")
        print()
    print("Count: ", num_matches, "/ 30")

"""
