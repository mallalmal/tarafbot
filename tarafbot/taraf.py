# -*- coding: utf-8 -*-

from enum import Enum
from player import Player
from deck import Deck, getActualCard
import discord

# MIN and MAX values are inclusive (>=, <=)
MIN_PLAYER = 2
MAX_PLAYER = 6
CHEAT_ON = True
DEBUG_ON = True


# Debug print
def dprint(string):
    if DEBUG_ON:
        print(string)


# Cheat print
def cprint(string):
    if CHEAT_ON:
        print(string)

async def initNormalEmbed(message, description):
    return discord.Embed(title=message, color=discord.Colour.dark_blue(), description=description)
async def initErrorEmbed(message, description):
    return discord.Embed(title=message, color=discord.Colour.red(), description=description)
async def initTealEmbed(message, description):
    return discord.Embed(title=message, color=discord.Colour.teal(), description=description)

async def initEmbedHeader(header, color='blue', description=None):
    switcher = {
        'blue': await initNormalEmbed(header, description),
        'red': await initErrorEmbed(header, description),
        'teal': await initTealEmbed(header, description)
    }
    embedHeader = switcher.get(color, await initNormalEmbed(header, description))
    return embedHeader

async def sendSimpleMessage(ctx, message, color='blue', description=None):
    embedMsg = await initEmbedHeader(message, color, description)
    await ctx.send(embed=embedMsg)

async def sendMsgToPlayer(message, user, color='blue', description=None):
    embedMsg = await initEmbedHeader(message, color, description)
    await user.send(embed=embedMsg)

class TurnState(Enum):
    WAITING = 1
    CALLING = 2
    PLAYING = 3
    PLAYING_OVER = 4


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
        self.lastMessage = None
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

    async def __startCallingPhase(self):
        dprint("Starting calling phase")
        self.turnState = TurnState.CALLING
        self.sumOfCalls = 0
        self.firstPlayer = 0
        self.currentPlayer = self.firstPlayer
        if self.currentTurn == 0:
            self.maxNbOfCalls = 1
        else:
            self.maxNbOfCalls = self.currentTurn
        # Reseting fold taken
        for player in self.players:
            player.foldTaken = 0
            player.call = "NA"
        self.lastMessage = None

    async def __startPlayingPhase(self):
        dprint("Starting playing phase")
        self.turnState = TurnState.PLAYING
        self.firstPlayer = 0
        self.currentPlayer = self.firstPlayer
        self.highestCard = 0
        self.highestCardOwner = None
        self.lastMessage = None

    async def __rearmCurrentTurn(self):
        if DEBUG_ON:
            self.currentTurn = 1
        else:
            self.currentTurn = self.nbOfTurns

    async def __deleteLastMsg(self):
        if self.lastMessage:
            await self.lastMessage.delete()

    async def setPlayerCall(self, playerName, call):
        player = await self.__getPlayerByName(playerName)
        player.call = int(call)

    async def incrementPlayerFoldTaken(self, playerName):
        player = await self.__getPlayerByName(playerName)
        player.foldTaken += 1

    async def isThisPlayerTurnToPlay(self, name):
        return await self.__getPlayerPosition(name) == self.currentPlayer

    async def isThisPlayerMaster(self, name):
        player = await self.__getPlayerByName(name)
        if player:
            return player.isMaster
        else:
            return False

    async def getPlayerList(self):
        playerList = []
        for player in self.players:
            playerList.append(player.name)
        return playerList

    async def printPlayersOrder(self, ctx):
        playerList = await self.getPlayerList()
        await sendSimpleMessage(ctx, "Ordre des joueurs", description=', '.join(playerList))

    async def printPlayersInfo(self, ctx):
        for player in self.players:
            await sendSimpleMessage(ctx, player.name + ", call: " + str(player.call) + ", pli(s): " + str(
                player.foldTaken) + ", shitPoints(s): " + str(player.shitPoints))

    async def printPlayersCards(self):
        for player in self.players:
            cprint(player.name + ":")
            cprint(player.cards)

    async def isThisANewPlayer(self, playerName, ctx):
        for player in self.players:
            if playerName == player.name:
                await sendSimpleMessage(ctx, "T'es déjà inscrit " + playerName, color='red')
                return False
        return True

    async def doesHeHaveThatCard(self, playerName, card):
        player = await self.__getPlayerByName(playerName)
        return int(await getActualCard(card)) in player.cards

    async def removeCardFromPlayer(self, playerName, card):
        player = await self.__getPlayerByName(playerName)
        player.cards.remove(int(await getActualCard(card)))
        player.cardPlayed = str(card)

    async def addPlayer(self, ctx):
        name = ctx.message.author.name
        if await self.isThisANewPlayer(name, ctx):
            if len(self.players) <= MAX_PLAYER:
                player = Player(name, bool(not self.players), ctx.message.author)
                self.players.append(player)
                await sendSimpleMessage(ctx, name + " a rejoint la partie. Vous êtes " + str(len(self.players)),
                                        description=', '.join(await self.getPlayerList()))
            else:
                await sendSimpleMessage(ctx, "Il y a déjà trop de joueurs !",
                                        color='red',
                                        description="maximum : " + str(len(self.players)))

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
        await self.deck.shuffle(self.players)
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
                        message.append(otherPlayers.name)
                        message.append(str(otherPlayers.cards[0]))
                await sendMsgToPlayer("Cartes sur le front des autres :", receiver.user, description=', '.join(message))
        else:
            for receiver in self.players:
                message = ['J' if card == 22 else str(card) for card in receiver.cards]
                await sendMsgToPlayer("Vos cartes :", receiver.user, description=', '.join(message))

    async def getNbOfCallsString(self):
        return "Nombre de call : " + str(self.sumOfCalls) + "/" + str(self.maxNbOfCalls)

    async def addNextCallerField(self, embedMsg):
        embedMsg.add_field(name="Prochain caller (!call x) :", value=self.players[self.currentPlayer].name, inline=False)

    async def addNextPlayerField(self, embedMsg):
        embedMsg.add_field(name="Prochain joueur (!play x) :", value=self.players[self.currentPlayer].name, inline=False)

    async def addFirstPlayerField(self, embedMsg):
        embedMsg.add_field(name="Premier joueur du tour (!play x) :", value=self.players[self.currentPlayer].name, inline=False)

    async def sendNewTurnMsg(self, ctx):
        embedMsg = await initEmbedHeader("Nouveau tour :", color='teal', description=await self.getNbOfCallsString())
        await self.addNextCallerField(embedMsg)
        await ctx.send(embed=embedMsg)

    async def startNewTurn(self, ctx):
        await self.dealCards()
        await self.sendCardsToPlayer()
        await self.__startCallingPhase()
        await self.sendNewTurnMsg(ctx)

    async def handleLastTurn(self, ctx):
        await sendSimpleMessage(ctx, "Dernier tour, allez on pose les cartes")
        for player in range(len(self.players)):
            await self.handleCardPlayed(ctx,
                                        self.players[self.currentPlayer].name,
                                        self.players[self.currentPlayer].cards[0])

    async def initCallingSummary(self):
        embedMsg = await initEmbedHeader("Résumé des calls :", description=await self.getNbOfCallsString())
        for caller in self.players:
            embedMsg.add_field(name=caller.name, value=str(caller.call))
        return embedMsg

    async def sendCallingPhaseMsg(self, ctx):
        embedMsg = await self.initCallingSummary()
        await self.addNextCallerField(embedMsg)
        return await ctx.send(embed=embedMsg)

    async def sendStartPlayingPhaseMsg(self, ctx):
        embedMsg = await self.initCallingSummary()
        await self.addFirstPlayerField(embedMsg)
        return await ctx.send(embed=embedMsg)

    async def nextPlayerCall(self, ctx):
        self.currentPlayer += 1
        if self.currentPlayer == len(self.players):
            await self.__deleteLastMsg()
            await self.__startPlayingPhase()
            await self.sendStartPlayingPhaseMsg(ctx)
            if self.currentTurn == 0:  # plays cards automatically on last turn since player don't know their cards
                await self.handleLastTurn(ctx)
        else:
            await self.__deleteLastMsg()
            self.lastMessage = await self.sendCallingPhaseMsg(ctx)

    async def handlePlayerCall(self, ctx, call):
        if self.turnState == TurnState.CALLING and await self.isThisPlayerTurnToPlay(ctx.message.author.name):
            if self.currentPlayer == len(self.players) - 1 and self.sumOfCalls + int(call) == self.maxNbOfCalls:
                await sendSimpleMessage(ctx, "Hé non ! Tu peux pas call " + str(call), color='red', description=await self.getNbOfCallsString())
            else:
                await self.setPlayerCall(ctx.message.author.name, call)
                self.sumOfCalls += int(call)
                await sendSimpleMessage(ctx, ctx.message.author.name + " call : " + str(call))
                await self.nextPlayerCall(ctx)

    async def addShitPointsField(self, embedMsg):
        for player in self.players:
            embedMsg.add_field(name=player.name,
                               value="+" + str(abs(player.call - player.foldTaken)) + " (" + str(player.shitPoints) + ")")

    async def addFinalShitPointsField(self, embedMsg):
        for player in self.players:
            embedMsg.add_field(name=player.name,
                               value=str(player.shitPoints))

    async def sendShitPointsMsg(self, ctx):
        embedMsg = await initEmbedHeader("Distrubution des shit points :")
        await self.addShitPointsField(embedMsg)
        return await ctx.send(embed=embedMsg)

    async def computeShitPoints(self, ctx):
        for player in self.players:
            if player.call != player.foldTaken:
                player.shitPoints += abs(player.call - player.foldTaken)
        await self.sendShitPointsMsg(ctx)

    async def sendEndOfGameMsg(self, ctx):
        embedMsg = await initEmbedHeader("PARTIE FINIE !", description="scores finaux :", color='red')
        await self.addFinalShitPointsField(embedMsg)
        await ctx.send(embed=embedMsg)

    async def nextDealer(self, ctx):
        if self.players[1] == self.firstDealer:
            await self.sendEndOfGameMsg(ctx)
            self.turnState = TurnState.PLAYING_OVER
        else:
            currentDealer = self.players[0]  # Current dealer is self.players[0]
            for player in range(len(self.players) - 1):
                self.players[player] = self.players[player + 1]
            self.players[len(self.players) - 1] = currentDealer
            await sendSimpleMessage(ctx, "Le nouveau dealer est " + self.players[0].name)
            await self.printPlayersOrder(ctx)
            await self.__rearmCurrentTurn()
            await self.startNewTurn(ctx)

    async def incrementCurrentPlayer(self):
        self.currentPlayer += 1
        if self.currentPlayer == len(self.players):  #
            self.currentPlayer = 0

    async def initPlayingSummary(self):
        embedMsg = await initEmbedHeader("Cartes jouées :",
                                         description="C'est " + self.highestCardOwner + " qui a la main avec " + str(self.highestCard))
        for player in self.players:
            embedMsg.add_field(name=player.name, value=str(player.cardPlayed))
        return embedMsg

    async def sendPlayingPhaseMsg(self, ctx, printNextPlayer=True):
        embedMsg = await self.initPlayingSummary()
        if printNextPlayer:
            await self.addNextPlayerField(embedMsg)
        return await ctx.send(embed=embedMsg)

    async def initFoldSummary(self):
        embedMsg = await initEmbedHeader("Résumé des plis :")
        for player in self.players:
            embedMsg.add_field(name=player.name, value=str(player.foldTaken) + "/" + str(player.call))
        return embedMsg

    async def sendEndOfFoldMsg(self, ctx):
        embedMsg = await self.initFoldSummary()
        await self.addFirstPlayerField(embedMsg)
        return await ctx.send(embed=embedMsg)

    async def nextPlayer(self, ctx):
        await self.incrementCurrentPlayer()
        if self.currentPlayer == self.firstPlayer:  # Fold is over
            await self.__deleteLastMsg()
            await self.sendPlayingPhaseMsg(ctx, printNextPlayer=False)
            await self.incrementPlayerFoldTaken(self.highestCardOwner)
            self.highestCard = 0
            if self.players[self.currentPlayer].cards:  # New fold
                await self.sendCardsToPlayer()
                self.firstPlayer = await self.__getPlayerPosition(self.highestCardOwner)
                self.currentPlayer = self.firstPlayer
                await self.sendEndOfFoldMsg(ctx)
            else:  # Turn is over
                await self.computeShitPoints(ctx)
                self.currentTurn -= 1
                if self.currentTurn >= 0:
                    await self.startNewTurn(ctx)
                else:
                    await self.nextDealer(ctx)
            for player in self.players:
                player.cardPlayed = "NA"
        else:  # There are still player playing this fold
            if self.currentTurn != 0:
                await self.__deleteLastMsg()
                self.lastMessage = await self.sendPlayingPhaseMsg(ctx)

    async def checkIfCardIsHigher(self, card, playerName):
        if int(card) > self.highestCard:
            self.highestCard = int(card)
            self.highestCardOwner = playerName

    async def handleCardPlayed(self, ctx, playerName, card):
        if self.turnState == TurnState.PLAYING and await self.isThisPlayerTurnToPlay(playerName):
            if await self.doesHeHaveThatCard(playerName, card):
                await self.removeCardFromPlayer(playerName, card)
                await self.checkIfCardIsHigher(card, playerName)
                await sendSimpleMessage(ctx, playerName + " joue : " + str(card))
                await self.nextPlayer(ctx)
            else:
                await sendSimpleMessage(ctx, "Tu n'as pas cette carte ...", color='red')
