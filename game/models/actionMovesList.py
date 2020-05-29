from django_enumfield import enum

class ActionMove(enum.Enum):
    createInitial = 0
    sanboxIncreaseCounter = 1
    startNewRound = 2

    nextTurn = 3
    nextGeneration = 4
    research = 5
    vyroba = 7

    __labels__ = {
        createInitial: "Vytvořit nový stav",
        sanboxIncreaseCounter: "Zvýšit counter",
        startNewRound: "Začít kolo",

        nextTurn: "Next turn",
        nextGeneration: "Next generation",
        research: "Zkoumat",
        vyroba: "Výroba"
    }