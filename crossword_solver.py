import itertools
import json
import os

import requests
import time
from collections import namedtuple
import wikipedia as wikipedia
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

articles = ("a", "an", "the", "of", "at", "in", "and", "on", "to")

# Constants
Clue = namedtuple('Clue', 'no label orient pos desc len ans clss')
ACROSS = 'across'
DOWN = 'down'
BLOCKED = '-'

# Global Variables
clues = []
board = [[(x, y) for x in range(5)] for y in range(5)]
label_coor = [(0, 0) for x in range(11)]


# Reads the crossword data including the board and the clues and the solutions from json file
def read_crossword(json_name):
    with open(json_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

        for b in data['board']:
            # x and y is swapped because of a mistake in the website
            x = b['coordinate']['y'] - 1
            y = b['coordinate']['x'] - 1
            if b['label'] != '':
                label_coor[int(b['label'])] = (x, y)
            if b['answer'] == '':
                board[y][x] = BLOCKED
            else:
                board[y][x] = b['answer']

        clue_index = 0
        for c in data['clues']:
            answer = ''
            orient = ACROSS if c['orientation'] == "ACROSS" else DOWN
            length = 0
            coor = label_coor[int(c['label'])]
            x = coor[0]
            y = coor[1]
            while not (y >= 5 or x >= 5 or board[y][x] == BLOCKED):
                answer += board[y][x]
                length += 1
                x += int(orient == ACROSS)
                y += int(orient == DOWN)
            coor = label_coor[int(c['label'])]
            classificationlst = classify_clue(c['clue'])
            clues.append(Clue(clue_index, c['label'], orient, coor, c['clue'], length, answer, classificationlst))
            clue_index += 1


def remove_special_characters(in_str):
    s = in_str.replace("___", "")
    s = s.replace("(", "")
    s = s.replace(")", "")
    s = s.replace("!", "")
    # s = s.replace("'", "")
    s = s.replace("-", " ")
    s = s.replace("\"", "")
    # s = s.replace("'s", "")
    s = s.replace(",", "")
    s = s.replace("?", "")
    return s


# Counts the occurences of the items in the total list
def calc_frequency(total):
    freq = {}
    for item in total:
        if item in freq:
            freq[item] += 1
        else:
            freq[item] = 1
    return freq


# Checks whether the css of the element exists
def css_exists(element, css):
    try:
        element.find_element_by_css_selector(css)
    except NoSuchElementException:
        return False
    return True


# Checks whether the clue is a cross reference clue
def is_cross_reference(word):
    ref = word.split("-")
    if len(ref) == 2:
        if ref[0].isnumeric() and (DOWN in ref[1].lower() or ACROSS in ref[1].lower()):
            return True
    return False


# Classifies the clue according to four types: "fill in the blank", "abbreviation", "plural", "cross-reference"
def classify_clue(clue_text):
    classifications = []
    if "___" in clue_text:
        classifications.append("fill in the blank")

    splitted = clue_text.split()
    for w in splitted:
        if w[len(w) - 1] == ".":
            classifications.append("abbreviation")
        if "they" in w.lower() or "and" == w.lower() \
                or w.lower() == "them" or "their" in w.lower():
            classifications.append("plural")

        if "-" in w:
            if is_cross_reference(w):
                classifications.append("cross-reference")

    return classifications

# Scrapes clues from the conceptnet website
def conceptnet(chrome_driver, clue_text, clue):
    print("Searching conceptnet for candidates...")
    candidate_list = []
    word_subsets = []
    splitted = clue_text.split()

    # Finds all the subsets of words of the clue
    for i in range(0, 2):
        word_subsets += list(itertools.combinations(splitted, i + 1))


    no_not_found = 0
    print(word_subsets)
    for subset in word_subsets:
        st = ""
        for s in subset:
            st += s + " "
        if subset[0] in articles or not st:
            continue

        chrome_driver.get("http://conceptnet.io/")
        search = chrome_driver.find_element_by_name("text")
        search.send_keys(st)
        search.send_keys(Keys.ENTER)
        h1 = chrome_driver.find_elements_by_css_selector("#main > div.header > div > div.pure-u-2-3 > h1")

        # If nothing is found on the website, break out of the loop and try the next word
        if h1[0].text == "Not found":
            no_not_found += 1
            if no_not_found == 10:
                no_not_found = 0
                break
            continue
        else:
            # Finding all the web elements according to their css selectors

            categories = chrome_driver.find_elements_by_css_selector("div.rel-grid > div.pure-g > div")
            num_categories = len(categories)
            i = 0
            while i in range(0, num_categories):
                css = "#main > div.content > div.rel-grid > div > div:nth-child({}) > h2".format(i + 1)
                header = chrome_driver.find_element_by_css_selector(css)
                if header.text == "Related terms":
                    more_css = "#main > div.content > div.rel-grid > div > div:nth-child({}) > ul > li.more > a".format(i + 1)
                    if css_exists(chrome_driver, more_css):
                        more = chrome_driver.find_element_by_css_selector(more_css)
                        main_window = chrome_driver.current_window_handle
                        link = more.get_attribute("href")
                        chrome_driver.execute_script("window.open();")
                        chrome_driver.switch_to_window(chrome_driver.window_handles[1])
                        chrome_driver.get(link)

                        weights = chrome_driver.find_elements_by_css_selector("div.weight")
                        ind_weight_reached = 1
                        for weight in weights:
                            w = float(weight.text.strip()[8:])
                            if w > 1.0:
                                ind_weight_reached += 1
                            else:
                                break

                        for j in range(1, ind_weight_reached):
                            start_css = "div.edge-list > table > tbody > tr:nth-child({}) > td.edge-start > span.term.lang-en > a".format(j)
                            if css_exists(chrome_driver, start_css):
                                start_edge = chrome_driver.find_element_by_css_selector(start_css)
                            else:
                                continue

                            candidate0 = start_edge.text
                            for art in articles:
                                if start_edge.text.startswith(art + " "):
                                    candidate0 = start_edge.text.replace(art + " ", "")

                            if candidate0 == clue_text:
                                continue

                            if len(candidate0) == int(clue.len):
                                candidate_list.append(candidate0.lower())

                        chrome_driver.close()
                        chrome_driver.switch_to_window(main_window)
                    i = num_categories
                else:
                    i += 1

    return list(set(candidate_list))

# Scrapes clues from the datamuse API
def datamuse(clue_text, clue):
    print("Searching datamuse for candidates...")
    response = requests.get("https://api.datamuse.com/words", params={"ml": clue_text})
    json_resp = response.json()
    candidate_list = []
    if len(json_resp) != 0:
        for resp in json_resp:
            if "score" in resp:
                if len(resp["word"]) == clue.len:
                    candidate_list.append(resp["word"].lower())
    return candidate_list


# Scrapes clues from the wikipedia API
def wiki(clue_text, clue):
    print("Searching wikipedia for candidates...")
    search = wikipedia.search(clue_text)
    cand_list = []
    for item in search:
        splitted = item.split()
        for s in splitted:
            if len(s) == clue.len:
                cand_list.append(s.lower())

    return cand_list

# Scrapes clues from the google search engine
def google(clue_text, clue, autoComplete=False):
    print("Searching google for candidates...")
    chrome_driver.get("https://www.google.com/")
    time.sleep(1)
    candidate_list = []
    search = chrome_driver.switch_to.active_element
    search.send_keys(clue_text)
    search.send_keys(Keys.ENTER)
    chrome_driver.get(chrome_driver.current_url + "&lr=lang_en")
    search = chrome_driver.find_element_by_name("q")
    search.clear()

    if autoComplete:
        # Scrapes the autocomplete suggestions
        splitted = clue_text.split()
        word_so_far = ""
        suggestions = None
        for word in splitted:
            word_so_far += word + " "
            search.send_keys(word + " ")
            if css_exists(chrome_driver, "#tsf > div:nth-child(2) > div.A8SBwf.emcav > div.UUbT9 > div.aajZCb > ul > li > div > div.sbtc > div.sbl1 > span"):
                suggestions = chrome_driver.find_elements_by_css_selector("#tsf > div:nth-child(2) > div.A8SBwf.emcav > div.UUbT9 > div.aajZCb > ul > li > div > div.sbtc > div.sbl1 > span")

            if suggestions:
                for sugg in suggestions:
                    cand = sugg.text
                    if cand in sugg.text and word_so_far in sugg.text:
                        cand = cand[cand.index(word_so_far) + len(word_so_far):]
                        cand = cand.strip()
                    if len(cand) == clue.len:
                        candidate_list.append(cand.lower())

    # Scrapes the search results after the clue has been written to search bar and entered
    search.clear()
    search.send_keys(clue_text)
    search.send_keys(Keys.ENTER)
    chrome_driver.get(chrome_driver.current_url + "&lr=lang_en")
    all = chrome_driver.find_elements_by_id("rso")
    for elem in all:
        lastword = ""
        for word in elem.text.split():
            if len(word) == clue.len:
                candidate_list.append(word.lower())


    return candidate_list

# According to the results coming from the hillclimb algorithm, the function searches for the unknown letters that hillclimb couldnt find in the board
def morewords(word):
    res = []
    chrome_driver.get("https://www.morewords.com/")
    if css_exists(chrome_driver, "input.mirror"):
        search = chrome_driver.find_element_by_css_selector("input.mirror")
        search.send_keys(word)
        search.send_keys(Keys.ENTER)
        if css_exists(chrome_driver, "#thecontent > div > div.col-md-8 > div > h1"):
            result_word = chrome_driver.find_element_by_css_selector("#thecontent > div > div.col-md-8 > div > h1")
            res.append(result_word)
        if css_exists(chrome_driver, "#thecontent > div.search > div > div.col-md-8 > div > p > a"):
            search_results = chrome_driver.find_elements_by_css_selector("#thecontent > div.search > div > div.col-md-8 > div > p > a")
            for r in search_results:
                ans = ''.join(i for i in r.text if not i.isdigit())
                res.append(ans)

    return res


def get_candidates():
    return candidates_list

with open('date.json', 'r', encoding='utf-8') as json_file:
        date = json.load(json_file)
json_filename = "puzzles/nytimes_puzzle_" + date + ".json"

read_crossword(json_filename)

options = Options()
options.headless = True
# options.add_argument("--mute-audio")

path = os.path.abspath("chromedriver")
chrome_driver = webdriver.Chrome(executable_path=path, options=options)
candidates_list = []

print('\nClues:')
for c in clues:
    print(c)

print('\nBoard:')
for b in board:
    print(b)
    

for ci in range(len(clues)):
    clue = clues[ci]
    print("\nSearching for clue ", ci)
    clue_text = remove_special_characters(clue.desc)

    datamuse_list = datamuse(clue_text, clue)
    concept_list = conceptnet(chrome_driver, clue_text, clue)
    wiki_list = wiki(clue_text, clue)
    google_list = []
    try:
        google_list = google(clue_text, clue, True)
    except Exception:
        pass
    
    total = concept_list + datamuse_list + wiki_list + google_list
    result_dict = calc_frequency(total)
    candidates_list.append(result_dict)
        


