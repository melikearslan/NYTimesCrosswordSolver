import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from datetime import date
import json

# CSS Variables
ok_button_css_list = [
    "#root > div > div > div.app-mainContainer--3CJGG > div > main > div.layout > div > "
    "div.Veil-veil--3oKaF.Veil-stretch--1wgp0 > div.Veil-veilBody--2x-ZE.Veil-autocheckMessageBody--31wj3 > div > "
    "article > div.buttons-modalButtonContainer--35RTh > button ",

    "#root > div > div > div.app-mainContainer--3CJGG > div > main > div.layout > div > "
    "div.Veil-veil--3oKaF.Veil-stretch--1wgp0 > div.Veil-veilBody--2x-ZE.Veil-standardMessageBody--1zizj > div > "
    "article > div.buttons-modalButtonContainer--35RTh > button "
]
solve_button_css = "#root > div > div > div.app-mainContainer--3CJGG > div > main > div.layout > div > div > ul > " \
                    "div.Toolbar-expandedMenu--2s4M4 > li:nth-child(2) > button "
puzzle_button_css = "#root > div > div > div.app-mainContainer--3CJGG > div > main > div.layout > div > div > ul > " \
                    "div.Toolbar-expandedMenu--2s4M4 > " \
                    "li.Tool-button--39W4J.Tool-tool--Fiz94.Tool-texty--2w4Br.Tool-open--1Moaq > ul > li:nth-child(3) "
reveal_button_css = "#root > div > div.ModalWrapper-wrapper--1GgyB.ModalWrapper-stretch--19Bif > " \
                    "div.ModalBody-body--3PkKz > article > div.buttons-modalButtonContainer--35RTh > " \
                    "button:nth-child(2) "
close_x_css = "#root > div > div.ModalWrapper-wrapper--1GgyB.ModalWrapper-stretch--19Bif > div.ModalBody-body--3PkKz " \
              "> span "
clues_css = "#root > div > div > div.app-mainContainer--3CJGG > div > main > div.layout > div > article > " \
            "section.Layout-clueLists--10_Xl > div "
board_css = "[data-group=\"cells\"] > g "

# JSON Variables
ny_times_data = {}
clues = []
board = []


def css_exists(element, css):
    try:
        element.find_element_by_css_selector(css)
    except NoSuchElementException:
        return False
    return True


def tag_exists(element, tag):
    try:
        element.find_element_by_tag_name(tag)
    except NoSuchElementException:
        return False
    return True


def get_clues(browser, css):
    print("Scraping all the clues...")
    clues_content = browser.find_elements_by_css_selector(css)
    for content in clues_content:
        temp = content.text + '\n'
        line, orientation, clue_number, clue_text = "", "", "", ""
        for character in temp:
            if character != '\n':
                line = line + character
            else:
                if line == "ACROSS" or line == "DOWN":
                    orientation = line
                elif line.isnumeric():
                    clue_number = line
                else:
                    clue_text = line

                if orientation and clue_number and clue_text:
                    clues.append({
                        'orientation': orientation,
                        'label': clue_number,
                        'clue': clue_text
                    })
                    clue_number, clue_text = "", ""
                line = ""
        print("Scraped {} clues.".format(orientation))


def get_board(browser, css):
    print("\nScraping the board and the answers...")
    cells_content = browser.find_elements_by_css_selector(css)
    x, y = 0, 0
    for content in cells_content:
        rect = content.find_element_by_tag_name("rect")
        fill = rect.value_of_css_property("fill")
        width = rect.value_of_css_property("width")
        height = rect.value_of_css_property("height")
        label = ""
        answer = ""
        if tag_exists(content, "text"):
            label_css = "[text-anchor=\"start\"]"
            answer_css = "[text-anchor=\"middle\"]"
            if css_exists(content, label_css):
                label = content.find_element_by_css_selector(label_css).text

            if css_exists(content, answer_css):
                answer = content.find_element_by_css_selector(answer_css).text

        if y % 5 == 0:
            y = 0
            x += 1
        y += 1

        board.append({
            'coordinate': {'x': x, 'y': y},
            'width': width,
            'height': height,
            'label': label,
            'fill': fill,
            'answer': answer
        })


def scrape():
    # options = Options()
    # options.headless = True
    # options.add_argument("--mute-audio")

    path = os.path.abspath("chromedriver")
    url = "https://www.nytimes.com/crosswords/game/mini"
    chrome_driver = webdriver.Chrome(executable_path=path)      # options=options,
    print("Connecting to https://www.nytimes.com/crosswords/game/mini ...")
    chrome_driver.get(url)
    print("CONNECTED")

    for button in ok_button_css_list:
        if css_exists(chrome_driver, button):
            chrome_driver.find_element_by_css_selector(button).click()

    print("Closed all popups.")

    solution_button = chrome_driver.find_element_by_css_selector(solve_button_css).click()
    puzzle_button = chrome_driver.find_element_by_css_selector(puzzle_button_css).click()
    reveal_button = chrome_driver.find_element_by_css_selector(reveal_button_css).click()
    x_button = chrome_driver.find_element_by_css_selector(close_x_css).click()

    print("Clicked on reveal button.")

    get_clues(chrome_driver, clues_css)
    print("Finished scraping the clues!")
    print("\nTHE CLUES:")
    for c in clues:
        print(c)

    get_board(chrome_driver, board_css)
    print("Finished scraping the board and the answers!")
    print("\nTHE BOARD:")
    for b in board:
        print(b)

    ny_times_data['clues'] = clues
    ny_times_data['board'] = board

    date_today = date.today()
    json_path = "puzzles/"
    json_file = "nytimes_puzzle_{}.json".format(date_today)

    print("\nDumping the information to {} ...".format(json_file))
    with open(json_path + json_file, 'w', encoding='utf-8') as outfile:
        json.dump(ny_times_data, outfile, indent=4)

    print("\nSCRAPING DONE!")
