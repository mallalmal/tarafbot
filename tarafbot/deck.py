from random import shuffle

async def getActualCard(card):
    if card == 0:
        return 22
    else:
        return card

class Deck:
    def __init__(self):
        self.cards = []

    async def shuffle(self, nbOfCards):
        self.cards = []
        for card in range(nbOfCards):
            self.cards.append(card + 1)
        shuffle(self.cards)