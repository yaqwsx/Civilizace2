from game.entities import Resource, Entities
from game.state import TeamId
from decimal import Decimal
from typing import List

D = Decimal

TEST_ENTITIES = Entities([
    Resource(id="res-prace", name="prace"),
    Resource(id="mat-drevo", name="Dřevo")
])

TEST_TEAMS: List[TeamId] = ["tym-zeleny", "tym-modry"]
