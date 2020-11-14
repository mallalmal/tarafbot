# -*- coding: utf-8 -*-

from enum import Enum
from random import shuffle

# MIN and MAX values are inclusive (>=, <=)
MIN_PLAYER = 2
MAX_PLAYER = 6
CHEAT_ON = True
DEBUG_ON = False


# Debug print
def dprint(string):
    if DEBUG_ON:
        print(string)

# Cheat print
def cprint(string):
    if CHEAT_ON:
        print(string)


class TurnState(Enum):
    WAITING = 1
    CALLING = 2
    PLAYING = 3
    PLAYING_OVER = 4


class Player:
    def __init__(self, name, isMaster, user):
        self.name = name
        self.isMaster = isMaster
        self.cards = []
        self.call = 0
        self.foldTaken = 0
        self.shitPoints = 0
        self.user = user


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


class GameContext:
    def __init__(self):
        # Recurent infos
        self.turnState = TurnState.WAITING
        self.players = []
        self.deck = Deck()
        self.nbOfTurns = 0
        self.currentTurn = 0
        self.currentPlayer = 0
        self.firstPlayer = 0
        self.firstDealer = None
        # DealerTurn based infos
        self.sumOfCalls = 0
        self.maxNbOfCalls = 99
        # Fold based infos
        self.highestCard = 0
        self.highestCardOwner = None
        print("Bot running")

    async def __getPlayerByName(self, name):
        for player in self.players:
            if player.name == name:
                return player

    async def __getPlayerPosition(self, name):
        position = 0
        for player in self.players:
            if player.name == name:
                return position
            position += 1
        return 99

    async def __startCallingPhase(self, ctx):
        dprint("Starting calling phase")
        self.turnState = TurnState.CALLING
        self.sumOfCalls = 0
        if self.currentTurn == 0:
            self.maxNbOfCalls = 1
        else:
            self.maxNbOfCalls = self.currentTurn
        await ctx.send("Nombre max de call : " + str(self.maxNbOfCalls))
        # Reseting fold taken
        for player in self.players:
            player.foldTaken = 0

    async def __startPlayingPhase(self, ctx):
        dprint("Starting playing phase")
        self.turnState = TurnState.PLAYING
        self.firstPlayer = 0
        self.currentPlayer = self.firstPlayer
        await self.printPlayersCalls(ctx)
        self.highestCard = 0
        self.highestCardOwner = None

    async def __rearmCurrentTurn(self):
        if DEBUG_ON:
            self.currentTurn = 1
        else:
            self.currentTurn = self.nbOfTurns

    async def setPlayerCall(self, playerName, call):
        player = await self.__getPlayerByName(playerName)
        player.call = int(call)

    async def incrementPlayerFoldTaken(self, playerName):
        player = await self.__getPlayerByName(playerName)
        player.foldTaken += 1

    async def isThisPlayerTurnToPlay(self, name):
        return await self.__getPlayerPosition(name) == self.currentPlayer

    async def printPlayersOrder(self, ctx):
        await ctx.send("Ordre des joueurs :")
        for player in self.players:
            await ctx.send(player.name)

    async def printPlayersInfo(self, ctx):
        for player in self.players:
            await ctx.send(player.name + ", call: " + str(player.call) + ", foldTaken: " + str(
                player.foldTaken) + ", shitPoints(s): " + str(player.shitPoints))

    async def printPlayersCalls(self, ctx):
        for player in self.players:
            await ctx.send(player.name + " a call: " + str(player.call))

    async def printPlayersCards(self):
        for player in self.players:
            cprint(player.name + ":")
            cprint(player.cards)

    async def isThisANewPlayer(self, playerName, ctx):
        for player in self.players:
            if playerName == player.name:
                await ctx.send("T'es déjà inscrit " + playerName)
                return False
        return True

    async def doesHeHaveThatCard(self, playerName, card):
        player = await self.__getPlayerByName(playerName)
        return int(await getActualCard(card)) in player.cards

    async def removeCardFromPlayer(self, playerName, card):
        player = await self.__getPlayerByName(playerName)
        player.cards.remove(int(await getActualCard(card)))

    async def addPlayer(self, ctx):
        name = ctx.message.author.name
        if await self.isThisANewPlayer(name, ctx):
            if len(self.players) <= MAX_PLAYER:
                player = Player(name, bool(not self.players), ctx.message.author)
                self.players.append(player)
                await ctx.send(name + " a rejoint la partie. Vous êtes " + str(len(self.players)))
            else:
                await ctx.send("Il y a déjà trop de joueurs ! (" + str(len(self.players)) + ")")

    async def shuffleDeck(self, nbOfCards):
        await self.deck.shuffle(nbOfCards)
        dprint("Cards shuffled")
        dprint(self.deck.cards)

    async def dealCards(self):
        if self.currentTurn == 0:
            nbOfCards = 1  # Deal 1 card for turn 0 (last turn)
            await self.shuffleDeck(21)  # No joker (22) on last turn
        else:
            nbOfCards = self.currentTurn
            await self.shuffleDeck(22)
        for cardsToDeal in range(nbOfCards):
            for player in self.players:
                player.cards.append(self.deck.cards.pop())

    async def prepareGame(self, ctx):
        self.nbOfTurns = 22 // len(self.players)
        await self.__rearmCurrentTurn()
        shuffle(self.players)
        await self.printPlayersOrder(ctx)
        self.currentPlayer = 0
        self.firstPlayer = 0
        self.firstDealer = self.players[0]

    async def sendCardsToPlayer(self):
        if self.currentTurn == 0:
            for receiver in self.players:
                message = []
                for otherPlayers in self.players:
                    if receiver.name != otherPlayers.name:
                        message.append(otherPlayers.cards[0])
                await receiver.user.send("Cartes sur le front des autres :")
                message = ['J' if card == 22 else card for card in message]
                await receiver.user.send(message)
        else:
            for player in self.players:
                message = ['J' if card == 22 else card for card in player.cards]
                await player.user.send(message)

    async def startNewTurn(self, ctx):
        await ctx.send("Nouveau tour")
        await self.dealCards()
        await self.sendCardsToPlayer()
        await self.__startCallingPhase(ctx)
        await ctx.send("Au tour de " + self.players[self.currentPlayer].name + " de call")

    async def handleLastTurn(self, ctx):
        await ctx.send("Dernier tour !")
        for player in range(len(self.players)):
            dprint("automatically playing for " + str(self.players[self.currentPlayer].name))
            await self.handleCardPlayed(ctx,
                                        self.players[self.currentPlayer].name,
                                        self.players[self.currentPlayer].cards[0])

    async def nextPlayerCall(self, ctx):
        dprint("nextPlayerCall, currentPlayer = " + str(self.currentPlayer) + " out of " + str(
            len(self.players) - 1) + " players")
        self.currentPlayer += 1
        if self.currentPlayer == len(self.players):
            await ctx.send("\nTous les joueurs ont parlés !")
            await self.__startPlayingPhase(ctx)
            if self.currentTurn == 0:  # plays cards automatically on last turn since player don't know their cards
                await self.handleLastTurn(ctx)
            else:
                await ctx.send("Au tour de " + self.players[self.firstPlayer].name + " de jouer la première carte")
        else:
            await ctx.send("Au tour de " + self.players[self.currentPlayer].name + " de call")

    async def handlePlayerCall(self, ctx, call):
        if self.turnState == TurnState.CALLING and await self.isThisPlayerTurnToPlay(ctx.message.author.name):
            if self.currentPlayer == len(self.players) - 1 and self.sumOfCalls + int(call) == self.maxNbOfCalls:
                await ctx.send("Hé non ! Tu peux pas call " + str(call) + ", la somme des call est de " + str(
                    self.sumOfCalls) + " sur " + str(self.maxNbOfCalls))
            else:
                await self.setPlayerCall(ctx.message.author.name, call)
                self.sumOfCalls += int(call)
                await ctx.send(
                    ctx.message.author.name + " call " + str(call) + ", total des call : " + str(self.sumOfCalls))
                await self.nextPlayerCall(ctx)

    async def computeShitPoints(self, ctx):
        await ctx.send("Distribution des shitpoints :")
        for player in self.players:
            if player.call != player.foldTaken:
                player.shitPoints += abs(player.call - player.foldTaken)
                await ctx.send("+" + str(abs(
                    player.call - player.foldTaken)) + " shitPoint(s) pour " + player.name + "... cheh !! T'en as " + str(
                    player.shitPoints))

    async def nextDealer(self, ctx):
        if self.players[1] == self.firstDealer:
            await ctx.send("Partie finie !")
            await self.printPlayersInfo(ctx)
            self.turnState = TurnState.PLAYING_OVER
        else:
            currentDealer = self.players[0]  # Current dealer is self.players[0]
            for player in range(len(self.players) - 1):
                self.players[player] = self.players[player + 1]
            self.players[len(self.players) - 1] = currentDealer
            await ctx.send("Le nouveau dealer est " + self.players[0].name)
            await self.printPlayersOrder(ctx)
            await self.__rearmCurrentTurn()
            await self.startNewTurn(ctx)

    async def incrementCurrentPlayer(self):
        self.currentPlayer += 1
        if self.currentPlayer == len(self.players):  #
            self.currentPlayer = 0

    async def nextPlayer(self, ctx):
        dprint("nextPlayer, currentPlayer = " + str(self.currentPlayer) + " out of " + str(
            len(self.players) - 1) + " players")
        await self.incrementCurrentPlayer()
        if self.currentPlayer == self.firstPlayer:
            await ctx.send("Pli terminé, " + self.highestCardOwner + " le prends avec " + str(self.highestCard))
            await self.incrementPlayerFoldTaken(self.highestCardOwner)
            self.firstPlayer = await self.__getPlayerPosition(self.highestCardOwner)
            self.currentPlayer = self.firstPlayer
            self.highestCard = 0
            if self.players[self.currentPlayer].cards:
                await ctx.send(
                    "Nouveau pli, au tour de " + self.players[self.currentPlayer].name + " de jouer la première carte")
            else:  # Turn is over
                await self.computeShitPoints(ctx)
                self.currentTurn -= 1
                if self.currentTurn >= 0:
                    await self.startNewTurn(ctx)
                else:
                    dprint("\nNouveau dealer :")
                    await self.nextDealer(ctx)
        else:  # There are still player playing this fold
            await ctx.send("Au tour de " + self.players[self.currentPlayer].name + " de jouer")

    async def checkIfCardIsHigher(self, ctx, card, playerName):
        if int(card) > self.highestCard:
            await ctx.send(playerName + " prends la main avec " + str(card))
            self.highestCard = int(card)
            self.highestCardOwner = playerName

    async def handleCardPlayed(self, ctx, playerName, card):
        if self.turnState == TurnState.PLAYING and await self.isThisPlayerTurnToPlay(playerName):
            if await self.doesHeHaveThatCard(playerName, card):
                print(playerName + " plays " + str(card))
                await self.removeCardFromPlayer(playerName, card)
                await self.checkIfCardIsHigher(ctx, card, playerName)
                await self.nextPlayer(ctx)
            else:
                await ctx.send("Tu n'as pas cette carte ...")
