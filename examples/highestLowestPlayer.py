# read n and j
n, j = map(int, input().split())
#your cards
cards=list(range(1,16))
# repeating for the whole game
while True:
    value = int(input())
    if value>0:
        #choose the highest card, so the last one since the list is ordered
        print(cards[-1])
        cards.pop(-1)
    else:
        #choose the lowest card
        print(cards[0])
        cards.pop(0)

    # reading the input but ignoring it
    submitted_numbers = list(map(int, input().split()))
