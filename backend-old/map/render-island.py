from island import pos_to_coord, generate_random_island, IslandType
from PIL import Image

import sys
import random

from argparse import ArgumentParser

from pathlib import Path
from typing import Dict, List

Tiles = Dict[str, List['Image']]


def load_tiles(path_to_tiles: Path) -> Tiles:
    tiles: Tiles = {}
    for tile in path_to_tiles.glob('*.png'):
        kind = tile.stem.split('-')[0]
        if kind not in tiles:
            tiles[kind] = []
        tiles[kind].append(Image.open(tile))
    return tiles


terrain_config = {
    'water': 'more',
    'forest': 'les',
    'shore': 'poust',
    'planes': 'louka',
    'mountain': 'skala',
    'mask': 'mask'
}


def get_tile(kind: str, tiles: Tiles, randomized: bool = True):
    if randomized:
        return random.choice(tiles[terrain_config[kind]])
    return tiles[terrain_config[kind]][0]


def render(layout):
    tiles = load_tiles(Path('./tiles/final'))

    mask = tiles['mask'][0]
    tile_width, tile_height = mask.size

    img = Image.new("RGBA", (tile_width * (layout.cols + 1), tile_height * layout.rows))
    for row in range(layout.rows):
        for col in range(layout.cols):
            coord = pos_to_coord(col, row)

            kind = layout.terrain[coord]
            tile = get_tile(kind, tiles)

            W = tile_width * col if row % 2 == 0 else tile_width * col + tile_width // 2
            H = row * (3 * tile_height // 4)

            img.paste(tile, (W, H), mask)
    return img


def main() -> None:

    parser = ArgumentParser(prog='render-island', description='Island Generator')
    parser.add_argument('-r', '--rows', metavar='rows', type=int, default=10)
    parser.add_argument('-c', '--columns', metavar='cols', type=int, default=10)
    parser.add_argument('-s', '--save', metavar='save_path', type=str)
    parser.add_argument('-b', '--border', metavar='border', type=int, default=2)
    parser.add_argument('--seed', metavar='seed', type=int)

    parser.add_argument('--sandy', action='append_const', dest='types', const=IslandType.Sandy)
    parser.add_argument('--foresty', action='append_const', dest='types', const=IslandType.Foresty)
    parser.add_argument('--hilly', action='append_const', dest='types', const=IslandType.Hilly)
    parser.add_argument('--rocky', action='append_const', dest='types', const=IslandType.Rocky)

    parser.add_argument('--rocks', metavar='rocks', type=int)
    parser.add_argument('--hills', metavar='hills', type=int)
    parser.add_argument('--earth', metavar='earth', type=int)
    parser.add_argument('--lakes', metavar='lakes', type=int)

    args = parser.parse_args()

    seed = args.seed if args.seed else random.randrange(sys.maxsize)
    print(f"seed: {seed}")
    random.seed(seed)

    types = []
    if args.types:
        types.extend(args.types)
    if args.hills:
        types.append(IslandType.Hilly)
    if args.rocks:
        types.append(IslandType.Rocky)

    island = generate_random_island(args.rows, args.columns, args.border, types
                                   , args.rocks, args.hills, args.earth, args.lakes)
    img = render(island)

    img.show()

    if args.save:
        img.save(args.save)


# .\render-island.py --sandy --foresty --hills 3 --seed 2021
# .\render-island.py --seed 4244450224836815611
if __name__ == '__main__':
    main()