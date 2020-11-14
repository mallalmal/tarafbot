
from enum import Enum
from discord.ext import commands
from taraf import GameContext, dprint, MIN_PLAYER

class GameState(Enum):
    NOT_STARTED = 1
    SIGNIN = 2
    STARTED = 3

class TarCog(commands.Cog):
    def __init__(self, bot):
        self.state = GameState.NOT_STARTED
        self.theGame = GameContext()
        self.channel = None
        self.bot = bot

    @commands.command()
    async def start(self, ctx):
        dprint("!start")
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.SIGNIN
            self.channel = ctx.message.channel.name
            await ctx.send("!join pour rejoindre")
        else:
            await ctx.send("Partie déjà en cours")

    @commands.command()
    async def stop(self, ctx):
        # TODO should check if is master
        if self.channel == ctx.message.channel.name:
            dprint("!stop")
            self.theGame = GameContext()
            self.state = GameState.NOT_STARTED

    @commands.command()
    async def join(self, ctx):
        if self.channel == ctx.message.channel.name:
            dprint("!join")
            if self.state == GameState.SIGNIN:
                await self.theGame.addPlayer(ctx)
            else:
                await ctx.send("Pas possible de rejoindre")

    @commands.command()
    async def go(self, ctx):
        dprint("!go")
        if self.state == GameState.SIGNIN:
            if len(self.theGame.players) >= MIN_PLAYER:
                self.state = GameState.STARTED
                await self.theGame.prepareGame(ctx)
                await self.theGame.startNewTurn(ctx)
            else:
                await ctx.send("Pas assez de joueurs")
        else:
            await ctx.send("Il faut d'abord ouvrir les inscriptions")

    @commands.command()
    async def call(self, ctx, call):
        dprint("!call " + str(call))
        if self.state == GameState.STARTED:
            await self.theGame.handlePlayerCall(ctx, call)

    @commands.command()
    async def play(self, ctx, card):
        dprint("!play " + str(card))
        if self.state == GameState.STARTED:
            if card == "J+":
                card = 22
            elif card == "J-":
                card = 0
            await self.theGame.handleCardPlayed(ctx, ctx.message.author.name, card)

    @commands.command()
    async def helpp(self, ctx):
        await ctx.send("Liste des commandes :\n"
                       "   !start     : créer la partie\n"
                       "   !join      : rejoindre la partie\n"
                       "   !go        : lancer la partie\n"
                       "   !call X    : call que vous aller prendre x plis\n"
                       "   !play X    : jouer la carte X (pour le joker J+ ou J-)\n"
                       "   !stop      : arrêter la partie")

    # for debug
    @commands.command()
    async def show(self, ctx):
        await self.theGame.printPlayersInfo(ctx)

    @commands.command()
    async def order(self, ctx):
        await self.theGame.printPlayersOrder(ctx)

    @commands.command()
    async def cheat(self, ctx):
        await self.theGame.printPlayersCards()
