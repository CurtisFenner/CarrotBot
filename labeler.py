import sys
import json
import random

from scrape import getQuestions


def manuallyLabel(course, choices):
    assert len(choices) >= 1

    questions = getQuestions(course)
    random.seed(0)
    random.shuffle(questions)

    with open(course + "-labels.json", "r") as f:
        manual_labels = json.load(f)
    import os
    for q in questions:
        if q.id in manual_labels:
            continue
        os.system("cls")
        print("#", str(len(manual_labels) + 1))
        print(q.title.encode(sys.stdout.encoding, errors='replace'))
        print(q.content.encode(sys.stdout.encoding, errors='replace'))
        print(q.id)
        print("." * 80)
        for i, v in enumerate(choices):
            print(str(i + 1) + ") ", v)
        print()
        label = input("Choose a label: ")
        try:
            label = int(label)
            if label < 1 or label > len(choices):
                break
            manual_labels[q.id] = choices[label - 1]
        except:
            break
    with open(course + "-labels.json", "w") as f:
        json.dump(manual_labels, fp=f)
    print("...done tagging")


def loadLabels(course):
    with open(course + "-labels.json", "r") as f:
        return json.load(f)
