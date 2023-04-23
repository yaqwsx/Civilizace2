from decimal import Decimal
from typing import Dict, Optional

from typing_extensions import override

from game.actions.actionBase import (TeamActionArgs, TeamInteractionActionBase,
                                     TileActionArgs)
from game.entities import Building, Resource


class BuildFinishArgs(TeamActionArgs, TileActionArgs):
    build: Building
    demolish: Optional[Building]


class BuildFinishAction(TeamInteractionActionBase):
    @property
    @override
    def args(self) -> BuildFinishArgs:
        assert isinstance(self._generalArgs, BuildFinishArgs)
        return self._generalArgs

    @property
    @override
    def description(self) -> str:
        return f"Kolaudace budovy {self.args.build.name} na poli {self.args.tile.name} ({self.args.team.name})"

    @override
    def cost(self) -> Dict[Resource, Decimal]:
        return self.state.world.buildDemolitionCost if self.args.demolish != None else {}

    @override
    def _initiateCheck(self) -> None:
        tileState = self.args.tileState(self.state)

        self._ensureStrong(self.args.build not in tileState.buildings,
                           f"Budova již na poli existuje a nelze postavit další.")
        self._ensureStrong(self.state.map.getOccupyingTeam(self.args.tile) == self.args.team,
                           f"Budovu nelze zkolaudovat, protože pole {self.args.tile.name} není v držení týmu.")

        self._ensureStrong(self.args.build in tileState.unfinished.get(self.args.team, []),
                           f"Budova {self.args.build.name} na poli {self.args.tile.name} neexistuje nebo nebyla dokončena.")

        self._ensureStrong(tileState.parcelCount < len(tileState.buildings) or self.args.demolish is not None,
                           f"Nedostatek parcel na poli {self.args.tile.name}. Je nutné vybrat budovu k demolici")
        self._ensureStrong(tileState.parcelCount >= len(tileState.buildings) or self.args.demolish is None,
                           f"Nelze zbourat budovu. Na poli {self.args.tile.name} jsou ještě volné parcely")

    @override
    def _commitSuccessImpl(self) -> None:
        tileState = self.args.tileState(self.state)

        if self.args.demolish is not None:
            tileState.buildings.remove(self.args.demolish)
            self._info += f"Na poli {self.args.tile.name} byla zbořena budova {self.args.demolish.name}."
        tileState.unfinished[self.args.team].remove(self.args.build)
        tileState.buildings.add(self.args.build)
        self._info += f"Stavba {self.args.build.name} na poli {self.args.tile.name} dokončena a zkolaudována."
