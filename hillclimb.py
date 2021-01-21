import json
import copy
import time
import random
from collections import namedtuple

date = input('Input date (yyyy-mm-dd): ')

with open('date.json', 'w') as outfile:
     json.dump(date, outfile)

# from solution_displayer import ret_board, upload_puzzle
from crossword_solver import morewords, get_candidates

#simplify the data
#json_name = input("\nEnter the name of the json file: ")

#a random state to start hill climbing
def random_state():
    res = copy.deepcopy(initial_state)
    for i in range(clue_count):
        res[i] = random.randrange( len(candidates[i]) )
    return res

#calculates the score for a board state 
#it mainly takes account if the crossing points of the selected candidates are matching
#it also slightly favours words with medium frequencies
def score(state): # lower is better
    res = 0
    curr_words = []
    curr_word_scores = []
    for i in range(clue_count):
        word = candidates[i][state[i]]
        curr_words.append(word)
        if word in candidate_data[i].keys():
            res -= 0.2 * int (  2 < candidate_data[i][word] < 8)
    for by in ind_board:
        for b in by:
            if len(b) == 2:
                l1 = curr_words[b[0][0]][b[0][1]].lower()
                l2 = curr_words[b[1][0]][b[1][1]].lower()
                res += int( l1 != l2 ) #if letters aren't matching
    return res

#a list for scores in selected candidates in a given state
def candidate_score(state):
    res = [ 0 for i in range(clue_count) ]
    curr_words = []
    for i in range(clue_count):
        curr_words.append(candidates[i][state[i]])
    for by in ind_board:
        for b in by:
            if len(b) == 2:
                l1 = curr_words[b[0][0]][b[0][1]].lower()
                l2 = curr_words[b[1][0]][b[1][1]].lower()
                res[b[0][0]] += int( l1 != l2  ) #if letters aren't matching
                res[b[1][0]] += int( l1 != l2  ) #if letters aren't matching
    return res


#number of incorrect words in a given state
def incorrect_words(state):
    res = 0
    for i in range(clue_count):
        if clues[i].ans.lower() != candidates[ i ][ state[i] ].lower():
            res += 1
    return res          

#this is a little hill climber brute with beam search 
# it tries to minimize the board score
# and works half of the time

def hill_climb(state, climb_length):
    iteration_count = 0
    max_plato = 4
    plato_streak = 0
    prevStates = [state]
    nextStates = []
    while iteration_count < climb_length and score(prevStates[0]) != 0 and plato_streak < max_plato:
        for s in prevStates:
            for i in range(clue_count):
                nextState = copy.deepcopy(s);
                for j in range(len(candidates[i])):
                    nextState[i] = j
                    nextStates.append(copy.deepcopy(nextState))
        nextStates.sort(reverse=False,key=score)
        temp = []
        
        #remove duplicates
        for s in nextStates:
            if temp[0:len(temp)] == s[0:len(s)]:
                nextStates.remove(s)
            else:
                temp = s

        #a random beam for a higher chance of success
        nslen = len(nextStates) / 20
        if score( nextStates[0] ) == score( prevStates[0] ):
            plato_streak += 1
        else:
            plato_streak = 0
        prevStates = nextStates[0:min(10,len(nextStates))] \
                    + nextStates[min(10,len(nextStates)) + (iteration_count % 10):min(100,len(nextStates)):10] \
                    + nextStates[min(100,len(nextStates))+ (iteration_count % 100):min(1000,len(nextStates)):100] \
                    + nextStates[min(1000,len(nextStates)) - iteration_count:len(nextStates):int(nslen)] \

        #reset
        print("\nIteration no: ", iteration_count, "Prevstates size: ", len(prevStates), "Best score: ", score( prevStates[0] ) )
        print("Plato_streak: ", plato_streak)
        print_board(prevStates[0])
        nextStates = []
        iteration_count += 1
    return prevStates[0]

#a function that calls hill climbing many times
#this solution was suitable for this particular case of hill climbing
#it decreases our chance of getting stuck in local maximums
def trekking_trip(hill_climb_count = 5, climb_length = 20):
    print("Printing candidates 7: ", candidates[7])
    global state, cand_scores
    min_score = 999
    state = initial_state
    best_state = state
    for i in range(hill_climb_count):
        print("\nHill climb: " , i)
        res = hill_climb(state, climb_length)
        if score(res) <= min_score:
            min_score = score(res)
            best_state = res
        if min_score == 0:
            break;
        state = random_state()
            
    state = best_state

#a function to print the board
#and other information
def print_board(state): # lower is better
    res = 0
    global curr_words
    curr_words = []
    for i in range(clue_count):
        curr_words.append(candidates[i][state[i]])
    ind = 0
    print("\nBoard: ")
    for y in range(5):
        pr = ""
        for x in range(5):
            l1 = " "
            l2 = " "
            b = ind_board[y][x]
            pr += "["
            if len(b) >= 1:
                l1 = curr_words[b[0][0]][b[0][1]].lower()
                pr += l1
            else:
                pr += " "
            if len(b) == 2:
                l2 = curr_words[b[1][0]][b[1][1]].lower()
                pr += "," + l2
            else:
                pr += "  "
            pr += '],'
            board[y][x] = (l1, l2)
        print(pr[0:len(pr)-1])
        
    global cand_scores
    cand_scores = candidate_score(state)
    print("\nWord scores (lower is better): ")
    for i in range(clue_count):
        print( candidates[i][ state[i] ], "\t: ", cand_scores[i], "Answer: ", clues[i].ans  )

    print( "Board score (lower is better): ", score(state) )
        #incorrect words function cheats by looking at the answers by the way
    print( "Incorrect word count (compares to the solution): ", incorrect_words(state) )
    time.sleep(0.5)
    return res

def get_board():
    return board

def get_curr_words():
    return curr_words


Clue = namedtuple('Clue','no label orient pos desc len ans')
ACROSS = 'across'
DOWN = 'down'
BLOCKED = '-'
clues = []
words = [ None for x in range(11) ]
board = [[ (x,y) for x in range(5) ] for y in range(5)]
ind_board = [[ [] for x in range(5)] for y in range(5)] #for storing clue letter indexes
clue_coor = [(0,0) for x in range(11)]

clue_count = 10
initial_state = [ 0 for w in words ]
state = initial_state
candidates = [ [] for w in words ]
candidate_date = []
cand_scores = [ 0 for i in range(10) ]
curr_words = [ "" for i in range(10) ]

def main():
    global clues
    global words
    global board
    global ind_board
    global clue_coor

    global clue_count
    global initial_state
    global state
    global candidates
    global candidate_date
    global cand_scores

    #gather board data for the selected date
    with open('puzzles/nytimes_puzzle_' + date + '.json', 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        
        for b in data['board']:
            #x and y is swapped because of a mistake in the website
            x = b['coordinate']['y'] - 1
            y = b['coordinate']['x'] - 1
            if b['label'] != '':
                clue_coor[int(b['label'])] = (x,y)
            if b['answer'] == '':
                board[y][x] = BLOCKED
            else:
                board[y][x] = b['answer']
            
        clue_index = 0
        for c in data['clues']:
            answer = ''
            orient = ACROSS if c['orientation'] == "ACROSS" else DOWN
            length = 0
            coor = clue_coor[int(c['label'])]
            x = coor[0]
            y = coor[1]
            while not (y >= 5 or x >= 5 or board[y][x] == BLOCKED ):
                ind_board[y][x].append( (clue_index, length) )
                answer += board[y][x]
                length += 1
                x += int( orient == ACROSS )
                y += int( orient == DOWN )  
            coor = clue_coor[int(c['label'])]
            clues.append( Clue(clue_index, c['label'], orient, coor, c['clue'], length, answer ) )
            clue_index += 1
        for i in range(clue_index):
            words[i] = clues[i].ans

    for i in range(clue_count):
        global candidate_data
        candidate_data = get_candidates()
        keys = candidate_data[i].keys()
        for k in keys:
            if k.isalpha():
                candidates[i].append(k)

    print('\nClues:')
    for c in clues:
        print(c)
          
    print('\nBoard:')
    for b in board:
        print(b)

    print('\nWord index Board:')
    for b in ind_board:
        print(b)


    state = copy.deepcopy(initial_state)
    trekking_trip()
    print_board(state)

    #this part results in the final board state
    for i in range(1):
        query = []
        second_worst_score = 0
        worst_score = 0
        for j in range(clue_count):
            if cand_scores[j] >= worst_score:
                second_worst_score = worst_score
                worst_score = cand_scores[i]
            elif cand_scores[j] > second_worst_score:
                second_worst_score = cand_scores[j]
        treshold = second_worst_score
        for i in range(clue_count):
            word = candidates[i][state[i]]
            query.append(list(word))
        for by in ind_board:
            for b in by:
                if len(b) == 2:
                    i1 = b[0][0]
                    i2 = b[1][0]
                    li1 = b[0][1]
                    li2 = b[1][1]
                    s1 = cand_scores[i1]
                    s2 = cand_scores[i2]

                    if s2 >= s1:
                        query[i2][li2] = query[i1][li1]
                    else:
                        query[i1][li1] = query[i2][li2]
        for i in range(clue_count):
            query[i] = "".join(query[i])
            candidates[i][0] = query[i]
        state = initial_state
        print_board(state)
        print("\nFinished solving the puzzle.")

