from django_enumfield import enum

class ActionMove(enum.Enum):
    createInitial = 0
    sanboxIncreaseCounter = 1
    startNewRound = 2

    nextTurn = 3
    nextGeneration = 4
    research = 5
    vyroba = 7
    foodSupply = 8

    godmode = 42
    sandbox = 99

    __labels__ = {
        createInitial: "SYSTEM: Vytvořit nový stav",
        sanboxIncreaseCounter: "DEBUD: Zvýšit counter",
        startNewRound: "DEBUG: Začít kolo",

        nextTurn: "Krmení",
        nextGeneration: "Next generation",
        research: "Zkoumat",
        vyroba: "Výroba",
        foodSupply: "Zásobování centra",


        godmode: "SYSTEM: Godmode",
        sandbox: "DEBUG: SANDBOX"
    }