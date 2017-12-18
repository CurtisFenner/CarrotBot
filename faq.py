from scrape import *
from query_linker import QueryLinker
import numpy as np
from numpy import linalg as LA

EECS370 = "islzyw4yldi4uy"
EECS497 = "j9embacbiat77"
EECS482 = "iou6tn9gf1z1eu"
questions = getQuestions(EECS370)
linker = QueryLinker(questions)

'''
print("#" * 50)
print("Method 1")

sim_matrix = np.zeros(shape=(len(questions),len(questions)))
sum_matrix = np.zeros(len(questions))

for i, q in enumerate(questions):
    if i % 100 == 0: print(i, "Completed")

    row = linker.getSimilarPosts(q)
    sim_matrix[i] = np.asarray(row)
    sum_matrix[i] = sum(row)

print()
argsort = np.argsort(-sum_matrix)
for i in argsort[0:3]:
    print(i)
    print(questions[i].title)
    print(questions[i].content)
    print()

print("#" * 50)
print("Method 2")
links = np.zeros(len(questions))
for i, q in enumerate(questions):
    if q.answer == "": continue
    linkMatch = re.findall('@(\d+)', q.answer)
    if not linkMatch: continue
    link = int(linkMatch[0])
    print(link)
    index = [j for j,quest in enumerate(questions) if quest.number == link]
    if any(index): links[index[0]] += 1

print()
argsort = np.argsort(-links)
for i in argsort[0:3]:
    print(questions[i].number)
    print(questions[i].title)
    print(questions[i].content)
    print()
'''

print("#" * 50)
print("Method 3")
from collections import defaultdict

indices = defaultdict(int)
for i, q in enumerate(questions):
    if i % 100 == 0: print(i, "Completed")

    row = linker.getSimilarPosts(q)
    argmax = np.argsort(-row)
    argmax = argmax[argmax != i]
    indices[argmax[0]] += 1

print()
top_indices = sorted(indices, key=indices.get, reverse=True)
for i in top_indices[0:10]:
    print("Index:", i, "Count:", indices[i])
    print("Number:", questions[i].number)
    print(questions[i].title)
    print(questions[i].content)
    print()
