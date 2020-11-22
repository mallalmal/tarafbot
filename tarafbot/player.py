class Player:
    def __init__(self, name, isMaster, user):
        self.name = name
        self.isMaster = bool(isMaster)
        self.cards = []
        self.call = 0
        self.foldTaken = 0
        self.shitPoints = 0
        self.user = user
        self.cardPlayed = "NA"

