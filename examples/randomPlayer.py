# import random to get randomness
from random import shuffle

# read n
n = int(input())

# Make a list of all cards 1,2,3,4,....,13,14,15
cards = list(range(1,16))

# shuffling the cards
shuffle(cards)

# laying out these cards in this order
for card in cards:
    # reading winnable card in the middle (and ignoring it)
    w = int(input())

    # play this card
    print(card)

    # reading the cards the other players played (and ignoring it)
    playedCards = list(map(int, input().split()))
