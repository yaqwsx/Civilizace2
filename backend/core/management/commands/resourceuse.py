from argparse import ArgumentParser
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from django.conf import settings
from django.core.management import BaseCommand

from core.management.commands.pullentities import ENTITY_SETS, setFilename
from game.entities import Entities, EntityBase, EntityWithCost, Resource, Tech, Vyroba
from game.entityParser import EntityParser


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("material", type=str, help="Resource id to show usage for")
        parser.add_argument("--set", "-s", type=str, default="GAME", choices=list(ENTITY_SETS), help="Entities set")
        parser.add_argument("--id", action="store_true", help="Show entity ids")

    def handle(self, material: str, set: str, id: bool, *args, **kwargs):
        assert set in ENTITY_SETS
        self.show_id = id
        targetFile = settings.ENTITY_PATH / setFilename(set)
        entities = EntityParser.load(targetFile)

        if material in entities.resources:
            self.print_resource_usage(entities, entities.resources[material])
            return
        if material in entities:
            raise RuntimeError(
                f"Entity exists but is a {type(entities[material])}, not {Resource}"
            )
        else:
            raise RuntimeError(f"Entity doesn't exist. Make sure to use full valid id")

    def entity_to_str(self, entity: EntityBase) -> str:
        return f"'{entity.name}'" if not self.show_id else f"'{entity.id}'"

    def res_amount_to_str(self, res_with_amount: Tuple[Resource, Decimal]) -> str:
        resource, amount = res_with_amount
        return f"{amount}x {self.entity_to_str(resource)}"

    def prettyprint_cost(self, entity: EntityWithCost) -> str:
        return f"{entity.points} points" + "".join(
            ", " + self.res_amount_to_str(res_amount)
            for res_amount in entity.cost.items()
        )

    def unlocked_by(self, entity: EntityWithCost, entities: Entities) -> list[Tech]:
        return sorted(
            (t for t in entities.techs.values() if entity in t.unlocks),
            key=lambda t: t.id,
        )

    def print_entity_usage_in(
        self,
        usage_entities: Iterable[EntityWithCost],
        resource: Resource,
        entities: Entities,
    ) -> None:
        for entity in usage_entities:
            if resource in entity.cost:
                reward_str = ""
                if isinstance(entity, Vyroba):
                    reward_str = f" => {self.res_amount_to_str(entity.reward)}"
                    for other_reward in entity.otherRewards:
                        reward_str += ", " + self.res_amount_to_str(other_reward)
                print(
                    f"  {entity.cost[resource]}x in {self.entity_to_str(entity)}: {self.prettyprint_cost(entity)}{reward_str}"
                )
                print(
                    f"    Unlocked by: {', '.join(map(self.entity_to_str, self.unlocked_by(entity, entities)))}"
                )

    def print_resource_usage(self, entities: Entities, material: Resource):
        if material.isTradableProduction:
            assert material.produces is not None
            raise RuntimeError(
                f"Resource is a production, use '{material.produces.id}' instead"
            )

        productions = [
            prod for prod in entities.resources.values() if prod.produces == material
        ]

        print()
        if len(productions) == 0:
            print(f"MATERIAL not produced by any PRODUCTION")
        elif len(productions) == 1:
            print(
                f"MATERIAL produced by PRODUCTION {self.entity_to_str(productions[0])}"
            )
        else:
            print(
                f"MATERIAL produced by PRODUCTIONS ({', '.join(map(self.entity_to_str, productions))})"
            )

        print()
        print("MATERIAL usage in TECH cost:")
        self.print_entity_usage_in(entities.techs.values(), material, entities)
        for prod in productions:
            print(f"PRODUCITON {self.entity_to_str(prod)} usage in TECH cost:")
            self.print_entity_usage_in(entities.techs.values(), prod, entities)

        print()
        print("MATERIAL usage in VYROBA cost:")
        self.print_entity_usage_in(entities.vyrobas.values(), material, entities)
        for prod in productions:
            print(f"PRODUCITON {self.entity_to_str(prod)} usage in VYROBA cost:")
            self.print_entity_usage_in(entities.vyrobas.values(), prod, entities)

        print()
        print("MATERIAL usage in BUILDING cost:")
        self.print_entity_usage_in(entities.buildings.values(), material, entities)
        for prod in productions:
            print(f"PRODUCITON {self.entity_to_str(prod)} usage in BUILDING cost:")
            self.print_entity_usage_in(entities.buildings.values(), prod, entities)

        print()
        print("MATERIAL usage in BUILDING UPGRADE cost:")
        self.print_entity_usage_in(
            entities.building_upgrades.values(), material, entities
        )
        for prod in productions:
            print(
                f"PRODUCITON {self.entity_to_str(prod)} usage in BUILDING UPGRADE cost:"
            )
            self.print_entity_usage_in(
                entities.building_upgrades.values(), prod, entities
            )

        print()
        print("MATERIAL created by:")
        for vyroba in entities.vyrobas.values():
            reward_res, reward_amount = vyroba.reward
            if material == reward_res:
                print(
                    f"  {reward_amount}x from {self.entity_to_str(vyroba)}: {self.prettyprint_cost(vyroba)}"
                )
                print(
                    f"    Unlocked by: {', '.join(map(self.entity_to_str, self.unlocked_by(vyroba, entities)))}"
                )
        print()
        print("MATERIAL additionally created by:")
        for vyroba in entities.vyrobas.values():
            for reward_res, reward_amount in vyroba.otherRewards:
                if material == reward_res:
                    print(
                        f"  {reward_amount}x from {self.entity_to_str(vyroba)}: {self.prettyprint_cost(vyroba)}"
                    )
                    print(
                        f"    Unlocked by: {', '.join(map(self.entity_to_str, self.unlocked_by(vyroba, entities)))}"
                    )

        for prod in productions:
            print(f"PRODUCTION {self.entity_to_str(prod)} created by:")
            for vyroba in entities.vyrobas.values():
                reward_res, reward_amount = vyroba.reward
                if prod == reward_res:
                    print(
                        f"  {reward_amount}x from {self.entity_to_str(vyroba)}: {self.prettyprint_cost(vyroba)}"
                    )
                    print(
                        f"    Unlocked by: {', '.join(map(self.entity_to_str, self.unlocked_by(vyroba, entities)))}"
                    )
            print(f"PRODUCTION {self.entity_to_str(prod)} additionally created by:")
            for vyroba in entities.vyrobas.values():
                for reward_res, reward_amount in vyroba.otherRewards:
                    if prod == reward_res:
                        print(
                            f"  {reward_amount}x from {self.entity_to_str(vyroba)}: {self.prettyprint_cost(vyroba)}"
                        )
                        print(
                            f"    Unlocked by: {', '.join(map(self.entity_to_str, self.unlocked_by(vyroba, entities)))}"
                        )
