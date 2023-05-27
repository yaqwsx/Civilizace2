from argparse import ArgumentParser
from typing import Iterable, Optional
from django.core.management import BaseCommand

from core.management.commands.pullentities import setFilename
from game.entities import Resource, Entities, EntityBase, EntityWithCost, Vyroba
from game.entityParser import EntityParser
from django.conf import settings


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("material", type=str, help='Resource id to show usage for')
        parser.add_argument("--set", "-s", type=str, default=None, help='Entities set')
        parser.add_argument("--id", action="store_true", help='Show entity ids')

    def handle(self, material: str, set: Optional[str], id: bool, *args, **kwargs):
        self.show_id = id
        set = 'GAME' if set is None else set
        targetFile = settings.ENTITY_PATH / setFilename(set)
        entities = EntityParser.load(targetFile)

        if material in entities.resources:
            self.print_resource_usage(entities, entities.resources[material])
            return
        if material in entities:
            raise RuntimeError(
                f'Entity exists but is a {type(entities[material])}, not {Resource}'
            )
        else:
            raise RuntimeError(
                f"Entity doesn't exist exists. Make sure to use full valid id"
            )

    def entity_to_str(self, entity: EntityBase) -> str:
        return f"'{entity.name}'" if not self.show_id else f"'{entity.id}'"

    def prettyprint_cost(self, entity: EntityWithCost) -> str:
        return f'{entity.points} points' + ''.join(
            f", {amount}x {self.entity_to_str(resource)}"
            for resource, amount in entity.cost.items()
        )

    def print_entity_usage_in(
        self, entities: Iterable[EntityWithCost], resource: Resource
    ) -> None:
        for entity in entities:
            if resource in entity.cost:
                reward_str = ''
                if isinstance(entity, Vyroba):
                    reward_res, reward_amount = entity.reward
                    reward_str = (
                        f' => {reward_amount}x {self.entity_to_str(reward_res)}'
                    )
                print(
                    f"  {entity.cost[resource]}x in {self.entity_to_str(entity)}: {self.prettyprint_cost(entity)}{reward_str}"
                )
                print(
                    f"    Unlocked by: {', '.join(self.entity_to_str(tech) for tech in entity.unlockedBy)}"
                )

    def print_resource_usage(self, entities: Entities, material: Resource):
        if material.isProduction:
            assert material.produces is not None
            raise RuntimeError(
                f"Resource is a production, use '{material.produces.id}' instead"
            )

        productions = [
            prod for prod in entities.productions.values() if prod.produces == material
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
        self.print_entity_usage_in(entities.techs.values(), material)
        for prod in productions:
            print(f"PRODUCITON {self.entity_to_str(prod)} usage in TECH cost:")
            self.print_entity_usage_in(entities.techs.values(), prod)

        print()
        print("MATERIAL usage in VYROBA cost:")
        self.print_entity_usage_in(entities.vyrobas.values(), material)
        for prod in productions:
            print(f"PRODUCITON {self.entity_to_str(prod)} usage in VYROBA cost:")
            self.print_entity_usage_in(entities.vyrobas.values(), prod)

        print()
        print("MATERIAL usage in BUILDING cost:")
        self.print_entity_usage_in(entities.buildings.values(), material)
        for prod in productions:
            print(f"PRODUCITON {self.entity_to_str(prod)} usage in BUILDING cost:")
            self.print_entity_usage_in(entities.buildings.values(), prod)

        print()
        print("MATERIAL created by:")
        for vyroba in entities.vyrobas.values():
            reward_res, reward_amount = vyroba.reward
            if material == reward_res:
                print(
                    f"  {reward_amount}x from {self.entity_to_str(vyroba)}: {self.prettyprint_cost(vyroba)}"
                )
                print(
                    f"    Unlocked by: {', '.join(self.entity_to_str(tech) for tech in vyroba.unlockedBy)}"
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
                        f"    Unlocked by: {', '.join(self.entity_to_str(tech) for tech in vyroba.unlockedBy)}"
                    )
