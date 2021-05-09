from hexgrid import Map

import sys
import random
import math
from enum import IntEnum, auto
from typing import List, Optional
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])


def pos_to_coord(col, row):
    if col % 2 == 0:
        return ( row + col // 2, col )
    return ( 1 + row + col // 2, col )


class IslandType(IntEnum):
    Sandy = auto()
    Foresty = auto()
    Hilly = auto()
    Rocky = auto()

class IslandMap( Map ):
    def __init__(self, rows, cols
                , border
                , types
                , rocks
                , hills
                , earth
                , lakes):
        super().__init__(rows, cols)
        self.terrain = dict()
        self.border = border
        self.rocks = rocks
        self.hills = hills
        self.earth = earth
        self.lakes = lakes
        self.types: List[IslandType] = types


    def random_point(self) -> Point:
        border = self.border
        x = random.randint(border, self.cols - border)
        y = random.randint(border, self.rows - border)
        return Point(x, y)


    def random_coords(self, n: int) -> List[Point]:
        return [pos_to_coord(*self.random_point()) for _ in range(n)]


    def generate_roots(self, kind: str, n: int) -> List[Point]:
        roots = []
        for coord in self.random_coords(n):
            roots.append(coord)
            self.terrain[coord] = kind
        return roots


    def generate(self):
        sandy = IslandType.Sandy in self.types
        foresty = IslandType.Foresty in self.types
        rocky = IslandType.Rocky in self.types
        hilly = IslandType.Hilly in self.types

        roots = []
        roots.extend(self.generate_roots('planes', self.earth))
        roots.extend(self.generate_roots('water', self.lakes))
        if hilly:
            roots.extend(self.generate_roots('mountain', self.hills))

        # add water roots to border
        rows, cols = self.rows, self.cols
        for row in range(rows):
            for col in range(cols):
                if col == 0 or col == cols - 1 or row == 0 or row == rows - 1:
                    coord = pos_to_coord(row, col)
                    roots.append(coord)
                    self.terrain[coord] = 'water'


        # fill map from roots
        terrain = self.terrain
        while roots:
            next_roots = []
            for root in roots:
                for neighbor in self.neighbors(root):
                    if not (neighbor in terrain):
                        terrain[neighbor] = terrain[root]
                        next_roots.append(neighbor)
            roots = next_roots

        # generate random rocks
        if rocky:
            self.generate_roots('mountain', self.rocks)

        # augment island tiles
        for row in range(rows):
            for col in range(cols):
                coord = pos_to_coord(row, col)
                # put sand on shores
                if sandy and terrain[coord] == 'planes':
                    for neighbor in self.neighbors(coord):
                        if terrain[neighbor] == 'water':
                            terrain[coord] = 'shore'
                            break
                # put forest around mountains
                if foresty and terrain[coord] == 'mountain':
                    for neighbor in self.neighbors(coord):
                        if terrain[neighbor] != 'water':
                            terrain[neighbor] = 'forest'
                # put forest inside planes
                if foresty and terrain[coord] != 'water':
                    count = 0
                    for neighbor in self.neighbors(coord):
                        if terrain[neighbor] == 'planes':
                            count += 1
                    if count > 4:
                        terrain[coord] = 'forest'


def generate_random_island( rows: int, cols: int, border: int
                          , types: List[IslandType]
                          , rocks: Optional[int]
                          , hills: Optional[int]
                          , earth: Optional[int]
                          , lakes: Optional[int]) -> IslandMap:

    # TODO pick better distributions
    rocks = rocks if rocks else random.randint(1, rows * cols // 4)
    hills = hills if hills else random.randint(1, rows * cols // 4)
    earth = earth if earth else random.randint(1, rows * cols // 4)
    lakes = lakes if lakes else random.randint(1, rows * cols // 4)

    if not types:
        def random_type():
            return IslandType(random.randrange(1, len(IslandType) + 1))

        n = random.randrange(1, len(IslandType))
        types = list(set([random_type() for _ in range(n)]))

    island = IslandMap(rows, cols, border, types, rocks, hills, earth, lakes)
    island.generate()

    return island
