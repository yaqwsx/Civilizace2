from PIL import Image, ImageDraw, ImageFont
import os
import tkinter
import tkinter.messagebox

class BreakException(Exception):
    pass
errors = []
def assertNoError():
    if len(errors) > 0: raise BreakException()

def dumpErrors():
    try:
        os.remove("ERROR.txt")
    except:
        None

    if len(errors) == 0:
        return False

    out = open("ERROR.txt", "w")
    out.write("Prosim opravit tyto chyby, aby sla vygenerovat mapa\n\n")

    for message in errors:
        out.write(message + "\n")
    return True

try:
    #============================
    # Preferences dialog
    window = tkinter.Tk()
    window.title("Map Generator configuration")

    class Pref:
        def __init__(self):
            self.x = tkinter.StringVar()
            self.y = tkinter.StringVar()
            self.w = tkinter.StringVar()
            self.h = tkinter.StringVar()
            self.show = tkinter.BooleanVar()
            self.indices = tkinter.BooleanVar()
    prefFile = open("presets.txt", "r")
    line = prefFile.readline()
    chunks = line.split(" ")
    prefFile.close()

    pref = Pref()
    pref.x.set(chunks[0])
    pref.y.set(chunks[1])
    pref.w.set(chunks[2])
    pref.h.set(chunks[3])
    pref.show.set(chunks[4] == "True")
    pref.indices.set(chunks[5] == "True")

    xLabel = tkinter.Label(window, text="X")
    xLabel.grid(column=0, row=0)
    xText = tkinter.Entry(window, width=10, textvariable=pref.x)
    xText.grid(column=1, row=0)

    yLabel = tkinter.Label(window, text="Y")
    yLabel.grid(column=0, row=1)
    yText = tkinter.Entry(window, width=10, textvariable=pref.y)
    yText.grid(column=1, row=1)

    wLabel = tkinter.Label(window, text="šířka")
    wLabel.grid(column=0, row=2)
    wText = tkinter.Entry(window, width=10, textvariable=pref.w)
    wText.grid(column=1, row=2)

    hLabel = tkinter.Label(window, text="výška")
    hLabel.grid(column=0, row=3)
    hText = tkinter.Entry(window, width=10, textvariable=pref.h)
    hText.grid(column=1, row=3)

    showCheck = tkinter.Checkbutton(window, text="Ukázat mapu", variable=pref.show)
    showCheck.grid(column=0, row=4)
    indicesCheck = tkinter.Checkbutton(window, text="Vykreslit indexy", variable=pref.indices)
    indicesCheck.grid(column=0, row=5)

    def closeWindow():
        window.destroy()
    button = tkinter.Button(window, text="OK", command=closeWindow, width=20, height=2)
    button.grid(column=0, row=6)
    button.focus()
    window.mainloop()

    prefFile = open("presets.txt", "w")
    prefFile.write(pref.x.get() + " " + pref.y.get() + " " + pref.w.get() + " " + pref.h.get() + " " + str(pref.show.get()) + " " + str(pref.indices.get()))
    prefFile.close()



    #============================
    # Load settings
    settingsFile = open("settings.txt", "r")
    for line in settingsFile:
        chunks = line.split()
        try:
            if chunks[0] == "tileOffsetX": tileOffsetX = int(chunks[1])
            if chunks[0] == "tileOffsetY": tileOffsetY = int(chunks[1])
            if chunks[0] == "lineOffsetX": lineOffsetX = int(chunks[1])
            if chunks[0] == "lineOffsetY": lineOffsetY = int(chunks[1])
            if chunks[0] == "tileZeroX": tileZeroX = int(chunks[1])
            if chunks[0] == "tileZeroY": tileZeroY = int(chunks[1])
            if chunks[0] == "pathToTiles": pathToTiles = chunks[1]
            if chunks[0] == "mapIndex": mapIndex = int(chunks[1])
        except Exception as e:
            errors.append("Chyba v nastaveni \"" + chunks[0] + "\"")

    requiredVariables = ["tileOffsetX", "tileOffsetY", "lineOffsetX", "lineOffsetY", "tileZeroX", "tileZeroY", "pathToTiles", "mapIndex"]
    for name in requiredVariables:
        if not name in globals().keys(): errors.append("Chybi nastaveni \"" + name + "\"")
    assertNoError()

    #============================
    # Load layout data
    def loadMapLayout(sheetId):
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        import json

        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name('google-sheet-key.json', scope)
        gc = gspread.authorize(credentials)

        wks = gc.open_by_url(
            "https://docs.google.com/spreadsheets/d/13fSjdYYp0hnL-CT8lhKCPHIsMxQGgd7EvcgbZSA1_-4/edit?usp=sharing")
        entitiesSheet = wks.get_worksheet(sheetId)

        result = entitiesSheet.get_all_values()
        return result
    mapLayout = loadMapLayout(mapIndex)

    #============================
    # Load tiles
    maskFilePath = pathToTiles + "/mask.png"
    mask = Image.open(pathToTiles + "/mask.png")

    tileNames = {}

    for line in mapLayout:
        for name in line:
            tileNames[name] = None

    tiles = {"": mask}
    for key in tileNames.keys():
        try:
            if key == "":
                continue
            tile = Image.open(pathToTiles + "/" + key + ".png")
            tiles[key] = tile
            if mask.size != tile.size:
                errors.append("Dilek " + key + str(tile.size) + " ma jine rozmery nez maska" + str(mask.size))
        except:
            errors.append("Nelze nacist soubor " + key + ".png")

    #============================
    def fromAlpha(a):
        val = 0
        for c in a:
            val *= 26
            i = ord(c) - 64
            if i > 26: i -= 32
            val += i
        return val
    def toAlpha(number):
        ret = chr( (number%26) + 65)
        if number >= 26:
            ret = chr((number//26) + 64) + ret
        return ret

    # Calculate size
    maxX = 0
    maxY = 0
    prefX = fromAlpha(pref.x.get()) - 1 # Align to sheet indices
    prefY = int(pref.y.get()) - 1 # Align to sheet indices
    prefW = int(pref.w.get())
    prefH = int(pref.h.get())

    for j, line in enumerate(mapLayout):
        if j< prefY: continue
        if j >= prefY + prefH: break

        X0 = tileZeroX
        Y0 = tileZeroY + (j-prefY) * lineOffsetY
        if j % 2:  X0 += lineOffsetX

        for i, tileName in enumerate(line):
            if tileName == "":
                continue
            if i < prefX: continue
            if i >= prefX + prefW: break

            X = X0 + (i-prefX) * tileOffsetX
            Y = Y0 + (i-prefY) * tileOffsetY

            print("Checking image " + str((i,j)) + " at " + str((X,Y)))

            if X > maxX: maxX = X
            if Y > maxY: maxY = Y

    maxX += mask.size[0]
    maxY += mask.size[1]

    result = Image.new("RGBA", (maxX, maxY))

    font = ImageFont.truetype("Verdana.ttf",26)
    d = ImageDraw.Draw(result)

    for j, line in enumerate(mapLayout):
        if j< prefY: continue
        if j >= prefY + prefH: break

        X0 = tileZeroX
        Y0 = tileZeroY + (j-prefY) * lineOffsetY
        if j % 2:  X0 += lineOffsetX

        if prefY % 2 == 1: X0 += lineOffsetX

        while X0 < 0: X0 += mask.size[0]

        for i, tileName in enumerate(line):
            if i < prefX: continue
            if i >= prefX + prefW: break

            X = X0 + (i-prefX) * tileOffsetX
            Y = Y0 + (i-prefY) * tileOffsetY

            if X < 0 or Y < 0:
                continue
            if tileName == "":
                continue

            tile = mask
            try:
                tile = tiles[tileName]
            except KeyError:
                print("Unknown tileName: " + str(tileName))
            result.paste(tile, (X,Y), mask)
            if pref.indices.get(): d.text((X + mask.size[0]//2 - 20, Y + mask.size[1]//2 - 14), toAlpha(i) + str(j+1), font=font, fill=(0, 0, 0))

    if pref.show.get():
        result.show()
    result.save("map.png")

except BreakException:
    None
except Exception as e:
    errors.append("Neocekavana chyba, napis Maarovi\n" + str(e))
    raise e

finally:
    if dumpErrors():
        # Error occured
        tkinter.messagebox.showerror("Pri generovani nastala chyba", "ERROR.txt\n" + str(errors))
    else:
        # Map generation successful
        None

