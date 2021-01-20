import difflib
import glob
import sys
import time
import pickle


class Node:
    def __init__(self, ch, source, line, sentence):
        # self.weight = 1
        # self.value = ch
        self.child = {}
        self.source_word = {source: [(sentence, line)]}
        self.len = 1

    # def add_line(self, src, l):
    #     if self.source.get(src) is not None:
    #         self.source[src].append(l)
    #     else:
    #         self.source[src] = [l]

    def add_word(self, src, sentence, l):
        if self.len >= 5:
            return
        if self.source_word.get(src) is not None:
            self.source_word[src].append((sentence, l))
        else:
            self.source_word[src] = [(sentence, l)]
        self.len += 1


class Trie:
    def __init__(self):
        self.child = {}

    def insert(self, word, source, line_num):
        current = self.child
        word = word.strip("\n")
        if len(word) == 0:
            return
        cleaned = word.translate(str.maketrans('', '', '#,;()./ \"\''))
        for ch in cleaned:
            if ch in current:
                # current[ch].add_line(source, line_num)
                current[ch].add_word(source, word, line_num)
                # current[ch].weight += 1
            else:
                current[ch] = Node(ch, source, line_num, word)
            current = current[ch].child
        current["#"] = 1

    # def build_all(self, start_node, found, sentences):
    #     if "#" in start_node.child:
    #         sentences.append((found, start_node.source, start_node.line))
    #         return found
    #     for i in start_node.child:
    #         self.build_all(start_node.child[i], found + i, sentences)

    def starts_with(self, prefix):
        current = self.child
        prev = None
        prefix = prefix.translate(str.maketrans('', '', '\n# \"\''))
        current_word = ""
        sentences = []
        found = True
        for ch in prefix:
            if ch in current:
                current_word += ch
                prev = current[ch]
                current = current[ch].child
        #     else:
        #         self.build_all(prev, current_word, sentences)
        #         found = False
        #         break
        # if found:
        #     self.build_all(prev, current_word, sentences)
        if len(sentences) < 5:
            i = 5
            sentences = []
            for src, val in prev.source_word.items():
                for item in val:
                    if i <= 0:
                        break
                    sentences.append((item[0], src, item[1]))
                    i -= 1

        return sentences


def penalty(score_base, indexes):
    penalty = 0
    for i in indexes:
        if i in score_base:
            penalty += score_base[i]
        else:
            penalty += score_base["def"]
    return penalty


def score(original, toCmp):
    base = 0
    swap_score = {0: 5, 1: 4, 2: 3, 3: 2, "def": 1}
    add_delete_score = {0: 10, 1: 8, 2: 6, 3: 4, "def": 2}
    deleted = set()
    added = set()
    # print('{} => {}'.format(toCmp[0], original))
    for i, s in enumerate(difflib.ndiff(toCmp[0], original)):
        if i > len(original):
            break
        if s[0] == ' ':
            base += 1
        elif s[0] == '-':
            # print(u'Delete "{}" from position {}'.format(s[-1], i))
            deleted.add(i)
        elif s[0] == '+':
            # print(u'Add "{}" to position {}'.format(s[-1], i))
            added.add(i)
    # print()
    base *= 2
    # print("base = ", base)

    if len(deleted):
        last_item = max(deleted)
        added = set([i - last_item for i in added])
    swapped = deleted.intersection(added)
    addedOrDeleted = (added - deleted) or (deleted - added)
    if len(swapped) > 0:
        base -= penalty(swap_score, swapped)
    if len(addedOrDeleted) > 0:
        base -= penalty(add_delete_score, addedOrDeleted)
    # print(base)
    return base


def get_file_array():
    file_arr = []
    i = 0
    for name in glob.glob('Archive/**/*.txt', recursive=True):
        i += 1
        file_arr.append(name)
    print(i, "files to proccess")
    return file_arr


def insert_input_from_data(trie, file_arr):
    i = 1
    for file_name in file_arr:
        line_num = 1
        with open(file_name, "r") as fp:
            for line in fp:
                trie.insert(line.lower(), file_name, line_num)
                line_num += 1
            if i % 10 == 0:
                print("finished file", i)
            i += 1

def replace_min(max_5, sentence, score):
    sorted(max_5, key=lambda item: item[1])  # sort by score
    if score > max_5[0][1]:
        max_5[0] = (sentence, score)


def online_phase(trie, start):
    res = trie.starts_with(start)
    max_5 = []
    sentence_score = {}
    if len(res):
        for r in res:  # keep max 5 results only no need for all dictionary and to sort
            sc = score(start, r)
            if len(max_5) < 5:
                max_5.append((r, sc))
            else:
                replace_min(max_5, r, sc)
    #         sentence_score[r] = score(start, r)
    # return sorted(sentence_score.items(), key=lambda item: item[1], reverse=True)
    return max_5


def print_suggestions(suggestions):
    count = min(len(suggestions), 5)
    if count:
        print("Here are", count, "suggestions:")
        for i in range(1, count + 1):
            print(str(i) + ".", suggestions[i - 1][0])
    else:
        print("There are no suggestions")


def run():
    trie = Trie()
    last = ""
    print("Loading files and preparing the system...")
    file_arr = get_file_array()
    tic = time.perf_counter()
    insert_input_from_data(trie, file_arr[:5])
    trie = pickle.load(open("save.p", "rb"))
    toc = time.perf_counter()
    #pickle.dump(trie, open("save.p", "wb"))

    print("finished in ", toc - tic, "time")
    print("The system is ready. Enter your text:")
    start = input().lower()
    while last != "#" and start != "#":
        start += last
        res = online_phase(trie, start)
        print_suggestions(res)
        print("Continue your search...")
        last = input(start).lower()
    #print("dictionary")
    # print(trie.child['c'].__dict__)


sys.setrecursionlimit(8000)
run()

