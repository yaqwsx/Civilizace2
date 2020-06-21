from django_enumfield import enum

class ActionMove(enum.Enum):
    createInitial = 0
    sanboxIncreaseCounter = 1
    startNewRound = 2

    nextTurn = 3
    nextGeneration = 4
    research = 5
    finishResearch = 6
    vyroba = 7
    foodSupply = 8
    setBuildingDistance = 9
    setTeamDistance = 10
    withdraw = 11
    trade = 12
    spendWork = 13
    addWonder = 15

    attack = 20

    godmode = 42
    sandbox = 99

    __labels__ = {
        nextTurn: "Krmení",
        research: "Zkoumat",
        finishResearch: "Dokončit zkoumání",
        vyroba: "Výroba",
        foodSupply: "Zásobování centra",
        setBuildingDistance: "Nastavit vzdálenost budov",
        setTeamDistance: "Nastavit vzdálenost týmů",
        withdraw: "Vybrat materiály ze skladu",
        trade: "Obchod",
        spendWork: "Zaplatit práci",
        addWonder: "Přidat základy divu",

        createInitial: "SYSTEM: Vytvořit nový stav",
        nextGeneration: "SYSTEM: Next generation",
        godmode: "SYSTEM: Godmode",

        attack: "Zaútočit",

        sandbox: "DEBUG: SANDBOX",
        sanboxIncreaseCounter: "DEBUG: Zvýšit counter",
        startNewRound: "DEBUG: Začít kolo"
    }