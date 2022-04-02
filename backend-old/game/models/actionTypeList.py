from django_enumfield import enum

class ActionType(enum.Enum):
    createInitial = 0
    sanboxIncreaseCounter = 1
    startNewRound = 2

    nextTurn = 3
    nextGeneration = 4
    research = 5
    finishResearch = 6
    vyroba = 7
    foodSupply = 8
    withdraw = 11
    trade = 12
    spendWork = 13
    enhancer = 14

    discoverIsland = 30
    exploreIsland = 31
    colonizeIsland = 32
    attackIsland = 33
    researchIsland = 34
    shareIsland = 35
    transferIsland = 36
    repairIsland = 37

    initialStickers = 40

    godmode = 42
    ensureEntitiyState = 43
    sandbox = 99

    addSticker = 100
    startTask = 101
    finishTask = 102

    maaraCounter = 103

    __labels__ = {
        nextTurn: "Krmení",
        research: "Zkoumat",
        finishResearch: "Dokončit zkoumání",
        vyroba: "Výroba",
        foodSupply: "Zásobování centra",
        withdraw: "Vybrat materiály ze skladu",
        trade: "Obchod",
        spendWork: "Zaplatit práci",
        enhancer: "Vylepšit výrobu",

        discoverIsland: "OSTROV: Hledat",
        exploreIsland: "OSTROV: Prozkoumat",
        colonizeIsland: "OSTROV: Kolonizovat",
        attackIsland: "OSTROV: Zaútočit",
        researchIsland: "OSTROV: Zkoumat technologii",
        shareIsland: "OSTROV: Nasdílet mapu",
        transferIsland: "OSTROV: Přenést vlastnictví",
        repairIsland: "OSTROV: Postav opevenění",

        initialStickers: "Udělit úvodní samolepky",

        createInitial: "SYSTEM: Vytvořit nový stav",
        nextGeneration: "SYSTEM: Next generation",
        godmode: "SYSTEM: Godmode",

        sandbox: "DEBUG: SANDBOX",
        sanboxIncreaseCounter: "DEBUG: Zvýšit counter",
        startNewRound: "DEBUG: Začít kolo",
        addSticker: "DEBUG: Udělit samolepku",
        startTask: "DEBUG: Začít úkol",
        finishTask: "DEBUG: Dokončit úkol",

        maaraCounter: "MAARA: Debug counter",

        ensureEntitiyState: "Přidej iniciální stavy nových entit",
    }