from scrape import getQuestions
from querytagger import QueryTagger
from labeler import loadLabels
import sys

eecs370_labels = [
    ["assembly", "registers", "instructions"],
    ["translation", "linker", "loader", "symbol table"],
    ["caller", "callee"],
    ["floating point", "endian", "sign extend", "endianness"],
    ["logic", "state machine", "gate"],
    ["datapath", "cycle"],
    ["pipeline", "hazard"],
    ["cache", "miss"],
    ["virtual"],
    ["logistics", "office hours", "autograder",
        "compiler", "discussion", "test files"]
]

def printAccuracyReport(key, tagger, questions, labels):
    print("== " + key + " " + "=" * 70)

    first_matches = 0
    second_matches = 0
    third_matches = 0
    num_tested = 0
    for q in questions:
        if q.id not in labels:
            continue
        expected = labels[q.id]

        details = tagger.getTopics(q)
        # Sort by probability
        details = sorted(details, key=lambda l: l[0], reverse=True)

        print(". " * 40)
        print(q.id)
        print(q.title.encode(sys.stdout.encoding, errors='replace'))
        print(q.content.encode(sys.stdout.encoding, errors='replace'))
        print()
        print("expected:", expected)
        print("got:     ", details[0][1])
        for d in details:
            print("\t", "%.2f" % d[0], d[1])

        num_tested += 1
        mentioned = []
        for e in expected:
            for l in eecs370_labels:
                if e in l:
                    mentioned.append(l)

        # Check for matches
        for i, x in enumerate(details):
            if x[1] in mentioned:
                match = i
                break
        if match < 3:  # Top 3
            print("MATCH!")
            third_matches += 1
            if match < 2:  # Top 2
                second_matches += 1
                if match < 1:  # Top 1
                    first_matches += 1
        else:
            print("NO MATCH!")
        print()
    print("  First Matches: ", first_matches, "/", num_tested,
          " = ", "{0:.0f}%".format(first_matches / num_tested * 100))
    print(" Second Matches: ", second_matches, "/", num_tested,
          " = ", "{0:.0f}%".format(second_matches / num_tested * 100))
    print("  Third Matches: ", third_matches, "/", num_tested,
          " = ", "{0:.0f}%".format(third_matches / num_tested * 100))

print("Loading course information...")
#COURSE = "islzyw4yldi4uy"
COURSE = "ij1u8xp4hz55gr"
questions = getQuestions(COURSE)
tagger = QueryTagger(questions, eecs370_labels)
labels = loadLabels(COURSE)

print("Generating accuracy report...")
printAccuracyReport(COURSE, tagger, questions, labels)
