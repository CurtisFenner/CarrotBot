from query_linker import *
from scrape import *

import statistics


def printAccuracyReport(factory, class_code, prints=True, CONFIDENCE=0.5):
    import time

    questions = getQuestions(class_code)
    linker = factory(questions)

    total = 0
    hits = 0
    percents = []
    ranks = []
    for post in questions:
        if post.answer == "":
            continue

        # If answer has "@", save the post number as link
        linkMatch = re.findall('@(\d+)', post.answer)
        if not linkMatch:
            continue
        link = int(linkMatch[0])
        if link >= post.number or not [x for x in questions if x.number == link]:
            continue

        BEFORE = time.time()

        # Find similar posts
        results, queryVector, tfv = linker.getSimilarPosts(post)

        # Remove posts that are older than current
        results = [m for m in results if m['question'].number < post.number]
        results = sorted(results, key=lambda x: x['similarity'], reverse=True)

        # Calculate weighted similarity of actual link
        best_similarity = results[0]['similarity']
        for result in results:
            question = result['question']
            similarity = result['similarity']
            if int(question.number) == int(link):
                percents.append(similarity / best_similarity)

        # Filter low-confidence results
        results = [r for r in results if r['similarity'] >= CONFIDENCE]

        print("Processing similarity took", time.time() -
              BEFORE, "seconds for", factory)

        if len(results) == 0:
            # Don't analyze if there were no confident results
            continue

        rank = None
        if prints:
            print("Post ID: ", post.number, "  Correct Link ID: ", link)

        shown = 0
        for i, result in enumerate(results):
            correct = int(result['question'].number) == int(link)
            if prints:
                if shown < 3 or correct:
                    shown = shown + 1
                    print(str(i + 1) + ". q",
                          result['question'].number, result['similarity'])
            if correct:
                rank = i + 1
                if prints:
                    print(link, "=>", "%.5f" %
                          result['similarity'], "rank", i + 1)
                    #losses = linker.getLosses(post, result['question'])
                    # for loss in sorted(losses, key=lambda x: abs(x[0]), reverse=True)[:5]:
                    #    print("\tloss", loss)

        if prints:
            print("Rank", rank)
        ranks.append(rank)

        total += 1

        # Check for matches
        hit = False
        for result in results[:3]:
            question = result['question']
            # print("%.5f" % similarity, question.number)
            if int(question.number) == int(link):
                hit = True
                hits += 1

        if prints:
            if hit:
                print("HIT")
            else:
                print("MISS")
            print()
            print("#" * 40)

    if prints:
        print("Accuracy: ", hits, " / ", total,
              " = ", int(hits / total * 100), "\b%")
        print("Weighted Similarity: ", sum(percents) / float(len(percents)))
        print()

    return {"percents": percents, "ranks": ranks, "hits": hits, "total": total}


courses = ["islzyw4yldi4uy", "ij1u8xp4hz55gr", "iou6tn9gf1z1eu"]

factories = [QueryLinker]  # [MpLinker]  # ,

mat = []

for factory in factories:
    row = []
    for course in courses:
        data = printAccuracyReport(factory, course, prints=True)

        rs = [rank for rank in data["ranks"] if rank != None]
        print("ranks:", rs)
        print("filtered out:", len(list(
            rank for rank in data["ranks"] if rank == None)))
        rank_mean = statistics.mean(rs)
        rank_median = statistics.median(rs)
        rank_stddev = statistics.stdev(rs)

        row.append({
            "hits": data["hits"] / data["total"] * 100,
            "mean": rank_mean,
            "median": rank_median,
        })
    mat.append(row)

print("-" * 80)

print("Hit in Top 3")
print("\t" + "\t".join(courses))
for i, row in enumerate(mat):
    left = str(factories[i])
    right = ["%.3f%%" % p["hits"] for p in row]
    print(left + "\t" + "\t".join(right))

print("")

print("Stats for Rank")
gap = [""] * (len(courses) - 1)
header = [""] + ["Mean"] + gap + ["Median"] + gap
print("\t".join(header))
print("\t" + "\t".join(courses * 2))
for i, row in enumerate(mat):
    left = str(factories[i])
    means = ["%.5f" % p["mean"] for p in row]
    medians = ["%.5f" % p["median"] for p in row]
    print(left + "\t" + "\t".join(means) + "\t" + "\t".join(medians))
