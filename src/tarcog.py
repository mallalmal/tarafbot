from enum import Enum
from discord.ext import commands
from taraf import GameContext, dprint, MIN_PLAYER, sendSimpleMessage


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
            await sendSimpleMessage(ctx, "!join pour rejoindre")
        else:
            await sendSimpleMessage(ctx, "Partie déjà en cours", color='red')

    @commands.command()
    async def stop(self, ctx):
        if self.channel == ctx.message.channel.name:
            if await self.theGame.isThisPlayerMaster(ctx.message.author.name):
                dprint("!stop")
                self.theGame = GameContext()
                self.state = GameState.NOT_STARTED
                await sendSimpleMessage(ctx, "La partie a été reset")
        await ctx.message.delete()

    @commands.command()
    async def join(self, ctx):
        if self.channel == ctx.message.channel.name:
            dprint("!join")
            if self.state == GameState.SIGNIN:
                await self.theGame.addPlayer(ctx)
            else:
                await sendSimpleMessage(ctx, "Pas possible de rejoindre", color='red')

    @commands.command()
    async def go(self, ctx):
        if self.channel == ctx.message.channel.name:
            dprint("!go")
            if self.state == GameState.SIGNIN:
                if len(self.theGame.players) >= MIN_PLAYER:
                    self.state = GameState.STARTED
                    await self.theGame.prepareGame(ctx)
                    await self.theGame.startNewTurn(ctx)
                else:
                    await sendSimpleMessage(ctx, "Pas assez de joueurs",
                                            color='red',
                                            description="minimum : " + str(MIN_PLAYER))
            else:
                await sendSimpleMessage(ctx, "Il faut d'abord ouvrir les inscriptions")

    @commands.command()
    async def call(self, ctx, call):
        if self.channel == ctx.message.channel.name:
            dprint("!call " + str(call))
            if self.state == GameState.STARTED:
                await self.theGame.handlePlayerCall(ctx, call)
        await ctx.message.delete()

    @commands.command()
    async def play(self, ctx, card):
        if self.channel == ctx.message.channel.name:
            dprint("!play " + str(card))
            if self.state == GameState.STARTED:
                if card == "J+":
                    card = 22
                elif card == "J-":
                    card = 0
                await self.theGame.handleCardPlayed(ctx, ctx.message.author.name, card)
        await ctx.message.delete()

    # for debug
    @commands.command()
    async def show(self, ctx):
        await self.theGame.printPlayersInfo(ctx)

    @commands.command()
    async def cheat(self, ctx):
        await self.theGame.printPlayersCards()
