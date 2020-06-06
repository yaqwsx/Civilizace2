#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup

domain = 'https://forgeofempires.fandom.com/'

def fullUrl(suffix):
    if suffix.startswith("/"):
        suffix = suffix[1:]
    return domain + suffix

def imageFromBuildingPage(pageUrl):
    try:
        page = requests.get(pageUrl)
        soup = BeautifulSoup(page.content, 'html.parser')
        figure = soup.find("figure", class_="pi-item pi-image")
        return figure.find("a")["href"]
    except:
        return None

def collectSpecialBuildings():
    page = requests.get(fullUrl("/wiki/Special_Buildings"))
    soup = BeautifulSoup(page.content, 'html.parser')
    images = set()
    for table in soup.find_all("table", class_="FoETable"):
        for row in table.find_all("tr"):
            cell = row.findChild()
            for link in cell.find_all("a", class_="image image-thumbnail"):
                images.add(link["href"])
    return images

def collectGreatBuildings():
    page = requests.get(fullUrl("/wiki/Great_Buildings"))
    soup = BeautifulSoup(page.content, 'html.parser')
    images = set()
    for table in soup.find_all("table", class_="AgeTable"):
        print(table)
        for link in table.find_all("a"):
            images.add(imageFromBuildingPage(fullUrl(link["href"])))
    return images

def collectTable(url, tableClass, column):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    images = set()
    for table in soup.find_all("table", class_=tableClass):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            print((len(cells)))
            if len(cells) > column:
                link = cells[column].find("a")
                images.add(imageFromBuildingPage(fullUrl(link["href"])))
    return images

def collectResidentialBuildings():
    return collectTable(fullUrl("/wiki/Residential_Buildings"), "AgeTable", 1)

def collectProductionBuildings():
    return collectTable(fullUrl("/wiki/Production_Buildings"), "AgeTable", 1)

def collectCultureBuildings():
    return collectTable(fullUrl("/wiki/Cultural_Buildings"), "AgeTable", 1)

def collectDecorationBuildings():
    return collectTable(fullUrl("/wiki/Decorations"), "AgeTable", 1)

def collectMilitaryBuildings():
    return collectTable(fullUrl("/wiki/Military_Buildings"), "FoETable", 0)

def collectGoodsBuildings():
    page = requests.get(fullUrl("/wiki/Goods_Buildings"))
    soup = BeautifulSoup(page.content, 'html.parser')
    images = set()
    for cell in soup.find_all("td"):
        if len(cell.find_all(recursive=False)) != 1:
            continue
        for link in cell.find_all("a", class_="image image-thumbnail"):
            images.add(link["href"])
    return images

def nameFromUrl(url):
    for elem in url.split("/"):
        if elem.endswith(".png") or elem.endswith(".jpg"):
            return elem[0:-4]

def downloadBuilding(url, directory):
    name = nameFromUrl(url)
    if not name: # Probably an animated gif, ignore it!
        return
    path = os.path.join(directory, name + ".png")
    with open(path, 'wb') as f:
        for chunk in requests.get(url):
            f.write(chunk)

images = set()
images |= collectSpecialBuildings()
images |= collectGreatBuildings()
images |= collectResidentialBuildings()
images |= collectProductionBuildings()
images |= collectCultureBuildings()
images |= collectDecorationBuildings()
images |= collectMilitaryBuildings()
images |= collectGoodsBuildings()

with open("images.txt", "w") as f:
    for item in images:
        if not item:
            continue
        f.write(item)
        f.write("\n")

# images = set()
# for line in open("images.txt").readlines():
#     images.add(line)
#     if not nameFromUrl(line):
#         print(line)

for item in images:
    if not item:
        continue
    downloadBuilding(item, "images")
