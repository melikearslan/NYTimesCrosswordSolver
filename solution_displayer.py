from tkinter import *
import json
from datetime import date, datetime
import crossword_scraper
import os
from hillclimb import main, get_board, curr_words
from threading import Thread

# global clues_across
clues_across = []
# global clues_down
clues_down = []
# global board
board = []

# Gets the today answer from NYTimes website
def get_today():
    print("\nGetting today's puzzle...")
    crossword_scraper.scrape()
    today = date.today()
    json_path = "puzzles/"
    json_name = "nytimes_puzzle_{}.json".format(today)
    with open(json_path + json_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        for c in data['clues']:
            if c['orientation'] == "ACROSS":
                clues_across.append(c)

            if c['orientation'] == "DOWN":
                clues_down.append(c)

        for b in data['board']:
            board.append(b)



# Uploads old puzzle data from folder
def upload_puzzle():
    global clues_across
    global clues_down
    global board
    with open('date.json', 'r', encoding='utf-8') as json_file:
        date = json.load(json_file)
    json_path = 'puzzles/nytimes_puzzle_' + date + '.json'
    if not os.path.exists(json_path):
        get_today()
        return     
    with open(json_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        for c in data['clues']:
            if c['orientation'] == "ACROSS":
                clues_across.append(c)

            if c['orientation'] == "DOWN":
                clues_down.append(c)

        for b in data['board']:
            board.append(b)

# Uploads the link of the old puzzle
def upload_puzzle_link(json_name):
    json_path = "puzzles/"
    with open(json_path + json_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        for c in data['clues']:
            if c['orientation'] == "ACROSS":
                clues_across.append(c)

            if c['orientation'] == "DOWN":
                clues_down.append(c)

        for b in data['board']:
            board.append(b)


def ret_board():
    return board

def ret_across():
    return clues_across


def ret_down():
    return clues_down

# Call main
def cont(event=None):
    main()

def clock():
    board = get_board()
    for y in range(5):
        for x in range(5):
            try:
                l1 = str(board[y][x][0]).upper()
                l2 = str(board[y][x][1]).upper()
            except Exception:
                print( board[y][x] )
            if l1 == l2:
                board_text[y][x]['text'] = l1
                board_text[y][x]['fg'] = 'green'
            else:
                board_text[y][x]['text'] = l1 + " " + l2
                board_text[y][x]['fg'] = 'red'
    our_main.after(100, clock) # run itself again after 1000 m

upload_puzzle()

## Display of the complete GUI
print("\nDisplaying the puzzle...")
our_main = Tk()
our_main.title("NY Times Crossword Puzzle by NEMESIS")
our_main.config(bg='#FFFFFF')
left = Frame(our_main, width=400, height=400, background='white', borderwidth=0, highlightthickness=0)
right = Frame(our_main, width=80, height=400, background='white', borderwidth=0, highlightthickness=0)
right_most = Frame(our_main, width=400, height=400, background='white', borderwidth=0, highlightthickness=0)
left.pack(side=LEFT)
right.pack(side=LEFT)
right_most.pack(side=LEFT)

board_canvas = Canvas(left, width=430, height=430, background='white', bd=0, highlightthickness=0)

now = datetime.now()
formatted_now = now.strftime("%B %d, %Y  %H:%M NEMESIS")
bottom_label_frame = Frame(left, width=50, height=50, background='white', pady=10)
bottom_label = Label(bottom_label_frame, text=formatted_now, background='white', font="franklin 11 bold")
bottom_label.pack(side=RIGHT, anchor=E)
bottom_label_frame.pack(anchor=E, side=BOTTOM)

width = 70
height = 70

our_board = board

for b in board:
    y0 = width * (b['coordinate']['x'] - 1)
    x0 = height * b['coordinate']['y']
    x1 = x0 + width
    y1 = y0 + height
    board_canvas.create_line(x0, y0, x0, y1, fill="light grey")
    board_canvas.create_line(x0, y0, x1, y0, fill="light grey")
    if b['fill'] == "rgb(0, 0, 0)":
        board_canvas.create_rectangle(x0, y0, x1, y1, fill='black', outline='grey')
    else:
        rect = board_canvas.create_rectangle(x0, y0, x1, y1, fill='white', outline='grey')
        if b['label']:
            board_canvas.create_text(x0 + 15, y0 + 15, text=b['label'], fill='black', font='arial 15 bold')
        if b['answer']:
            board_canvas.create_text(x0 + width / 2, y0 + height / 2 + 10, text=b['answer'], fill='blue',
                                     font='arial 25')

board_canvas.pack(side=LEFT)

clues_frame = Frame(right, width=80, height=700, background='white', highlightthickness=0)

clues_across_frame = Frame(clues_frame, width=50, height=6, background='white', padx=20, highlightthickness=0)
label_across_frame = Frame(clues_frame, width=50, height=6, background='white', pady=0, padx=20)
across_text_area = Text(clues_across_frame, width=80, height=6, background='white', bd=0, highlightthickness=0)
across_label = Label(label_across_frame, text='ACROSS', background='white', font="franklin 14 bold")

label_across_frame.pack(anchor=NW)
clues_across_frame.pack(side=TOP)
across_label.pack(side=LEFT)
across_text_area.pack(fill=BOTH)

clues_down_frame = Frame(clues_frame, width=80, height=6, background='white', padx=20)
label_down_frame = Frame(clues_frame, width=50, height=6, background='white', pady=10, padx=20)
down_text_area = Text(clues_down_frame, width=80, height=6, background='white', bd=0, highlightthickness=0)
down_label = Label(label_down_frame, text='DOWN', background='white', font="franklin 14 bold")

label_down_frame.pack(anchor=NW)
clues_down_frame.pack(side=TOP)
down_label.pack(side=LEFT)
down_text_area.pack(fill=BOTH)

line_ind = 0
label_end = 0
char_ind = 0
for clue in clues_across:
    label_end = 0
    char_ind = 0
    text = clue['label'] + "     " + clue['clue'] + "\n"
    across_text_area.insert(END, text)
    for c in text:
        if c == "     ":
            break
        label_end += 1

    char_ind = label_end + 1
    line_ind += 1

    label_tag_start = str(line_ind) + ".0"
    label_tag_end = str(line_ind) + "." + str(char_ind)
    across_text_area.tag_add("label", label_tag_start, label_tag_end)

    clue_tag_start = str(line_ind) + "." + str(char_ind)
    clue_tag_end = str(line_ind) + "." + str(len(clue['label'] + " " + clue['clue']))
    across_text_area.tag_add("clue", clue_tag_start, clue_tag_end)
    across_text_area.tag_config("label", font="franklin 12 bold")
    across_text_area.tag_config("clue", font="franklin 11")

line_ind = 0
label_end = 0
char_ind = 0
for clue in clues_down:
    label_end = 0
    char_ind = 0
    text = clue['label'] + "     " + clue['clue'] + "\n"
    down_text_area.insert(END, text)
    for c in text:
        if c == "     ":
            break
        label_end += 1

    char_ind = label_end + 1
    line_ind += 1

    label_tag_start = str(line_ind) + ".0"
    label_tag_end = str(line_ind) + "." + str(char_ind)
    down_text_area.tag_add("label", label_tag_start, label_tag_end)

    clue_tag_start = str(line_ind) + "." + str(char_ind)
    clue_tag_end = str(line_ind) + "." + str(len(clue['label'] + " " + clue['clue']))
    down_text_area.tag_add("clue", clue_tag_start, clue_tag_end)
    down_text_area.tag_config("label", font="franklin 12 bold")
    down_text_area.tag_config("clue", font="franklin 11")
clues_frame.pack()

our_board_canvas = Canvas(right_most, width=500, height=430, background='white', bd=0, highlightthickness=0)

width = 70
height = 70

board_text = [ [ None for x in range(5) ] for y in range(5) ]


for b in our_board:
    x = b['coordinate']['y'] - 1
    y = b['coordinate']['x'] - 1
    y0 = width *  (b['coordinate']['x'] - 1)
    x0 = height * (b['coordinate']['y'] - 1)
    x1 = x0 + width
    y1 = y0 + height
    our_board_canvas.create_line(x0, y0, x0, y1, fill="light grey")
    our_board_canvas.create_line(x0, y0, x1, y0, fill="light grey")
    if b['fill'] == "rgb(0, 0, 0)":
        our_board_canvas.create_rectangle(x0, y0, x1, y1, fill='black', outline='grey')
    else:
        rect = our_board_canvas.create_rectangle(x0, y0, x1, y1, fill='white', outline='grey')
        if b['label']:
            our_board_canvas.create_text(x0 + 15, y0 + 15, text=b['label'], fill='black', font='arial 15 bold')
        # if b['answer']:
            # our_board_canvas.create_text(x0 + width / 2, y0 + height / 2 + 10, text=b['answer'], fill='blue',
                                    # font='arial 25')
    board_text[y][x] = Label(our_board_canvas, text=" ", fg='blue', bg='white', font='arial 22' )
    if b['fill'] == "rgb(0, 0, 0)":
        board_text[y][x]['bg'] = 'black'
    board_text[y][x].place( relx = (1 + 2*x) / 12.0, rely = (1 + 2*y) / 12.0, anchor = 'center')
our_board_canvas.pack(side=LEFT)
search_thread = Thread(target=main, daemon=True)
search_thread.start()
clock()
our_main.mainloop()