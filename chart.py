import os
from collections import defaultdict
import sys
import time

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize

sid = SentimentIntensityAnalyzer()


def questionPositivity(question):
    """RETURNS a tuple (min, mean, max) positivity for question"""
    text = question.title + ". " + question.content
    sentences = tokenize.sent_tokenize(text)
    low = 1
    high = 0
    mean = 0
    for sentence in sentences:
        p = sid.polarity_scores(sentence)
        x = p['compound']
        low = min(low, x)
        high = max(high, x)
        mean += x
    out = mean / len(sentences)
    return out


def questionsByDate(questions):
    out = defaultdict(lambda: [])
    for question in questions:
        date = question.time[0:10]
        out[date].append(question)
    return out

# Time to beat: 22.68s


def positivityOverTimeChart(allQuestions):
    byDate = questionsByDate(allQuestions)
    out = {}
    for date, qs in byDate.items():
        rs = [questionPositivity(q) for q in qs]
        out[date] = {
            'min': min(rs),
            'mean': sum(rs) / len(rs),
            'count': len(qs),
            'max': max(rs),
        }
    return out


def topicsOverTimeChart(questions, tagger):
    labels = tagger.listTopics()
    tns = list(map(lambda x: str(x), labels))
    chart = defaultdict(lambda: defaultdict(lambda: 0))

    begin = time.time()
    tags = tagger.getTopicsMany(questions)
    for i, question in enumerate(questions):
        date = question.time[0:10]
        ts = tags[i]  # tagger.getTopics(question)
        totalWeight = sum(map(lambda x: x[0], ts))
        limitWeight = totalWeight / len(tns)
        for i, tag in enumerate(ts):
            tagLabel = tag[1]
            tagAmount = tag[0]
            tagKey = ", ".join(tagLabel)
            if tag[0] >= limitWeight:
                # Only include confident tags
                # (guaranteed at least one for each question)
                chart[date][tagKey] += tag[0]

    return chart


def viewsOverTime(questions):
    chart = defaultdict(lambda: {'posts': 0, 'views': 0})
    for question in questions:
        date = question.time[0:10]
        chart[date]['posts'] += 1
        chart[date]['views'] += question.views
    return chart
