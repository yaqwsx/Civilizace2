import _ from "lodash";
import { classNames, LoadingOrError } from ".";
import {
    BuildingEntity,
    BuildingTeamEntity,
    BuildingUpgradeEntity,
    BuildingUpgradeTeamEntity,
    EntityBase,
    MapTileEntity,
    MapTileTeamEntity,
    Team,
    TeamAttributeEntity,
    TeamAttributeTeamEntity,
} from "../types";
import { useEntities, useTeamEntities } from "./entities";

function EntitySelectForm<TEntity extends EntityBase>(props: {
    emptyLabel: string;
    value?: TEntity;
    entities: TEntity[];
    onChange: (id?: TEntity) => void;
    filter?: (value: TEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<TEntity>>;
    className?: string;
}): JSX.Element {
    let entities = _.filter(props.entities, props.filter).sort(
        (a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id)
    );
    if (!_.isNil(props.sortBy)) {
        entities = _.sortBy(entities, props.sortBy);
    }

    return (
        <select
            className={classNames("select field", props.className)}
            value={props.value?.id}
            onChange={(e) =>
                props.onChange(
                    props.entities.find((value) => value.id === e.target.value)
                )
            }
        >
            <option value="">{props.emptyLabel}</option>
            {props.entities.map((e) => (
                <option key={e.id} value={e.id}>
                    {e.name}
                </option>
            ))}
        </select>
    );
}

function EntitySelect<TEntity extends EntityBase>(props: {
    entityType: string;
    emptyLabel: string;
    value?: TEntity;
    onChange: (newValue?: TEntity) => void;
    filter?: (value: TEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<TEntity>>;
    className?: string;
}): JSX.Element {
    const { data, error } = useEntities<TEntity>(props.entityType);
    if (!data) {
        return (
            <LoadingOrError
                error={error}
                message={`Nemůžu načíst entity (${props.entityType})`}
            />
        );
    }
    return (
        <EntitySelectForm
            emptyLabel={props.emptyLabel}
            value={props.value}
            entities={Object.values(data)}
            onChange={props.onChange}
            filter={props.filter}
            sortBy={props.sortBy}
            className={props.className}
        />
    );
}

function TeamEntitySelect<TEntity extends EntityBase>(props: {
    entityType: string;
    emptyLabel: string;
    team: Team | undefined;
    value?: TEntity;
    onChange: (newValue?: TEntity) => void;
    filter?: (value: TEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<TEntity>>;
    className?: string;
}): JSX.Element {
    const { data, error } = useTeamEntities<TEntity>(
        props.entityType,
        props.team
    );
    if (!data) {
        return (
            <LoadingOrError
                error={error}
                message={`Nemůžu načíst týmové entity (${props.entityType})`}
            />
        );
    }
    return (
        <EntitySelectForm
            emptyLabel={props.emptyLabel}
            value={props.value}
            entities={Object.values(data)}
            onChange={props.onChange}
            filter={props.filter}
            sortBy={props.sortBy}
            className={props.className}
        />
    );
}
export function TileSelect(props: {
    value?: MapTileEntity;
    onChange: (tile?: MapTileEntity) => void;
    filter?: (value: MapTileEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<MapTileEntity>>;
    className?: string;
}) {
    return (
        <EntitySelect<MapTileEntity>
            entityType="tiles"
            emptyLabel="Žádné políčko"
            {...props}
        />
    );
}

export function TileTeamSelect(props: {
    team: Team;
    value?: MapTileTeamEntity;
    onChange: (tile?: MapTileTeamEntity) => void;
    filter?: (value: MapTileTeamEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<MapTileTeamEntity>>;
    className?: string;
}) {
    return (
        <TeamEntitySelect<MapTileTeamEntity>
            entityType="tiles"
            emptyLabel="Žádné políčko"
            {...props}
        />
    );
}

export function BuildingSelect(props: {
    value?: BuildingEntity;
    onChange: (value?: BuildingEntity) => void;
    filter?: (value: BuildingEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<BuildingEntity>>;
    className?: string;
}) {
    return (
        <EntitySelect<BuildingEntity>
            entityType="buildings"
            emptyLabel="Žádná budova"
            {...props}
        />
    );
}

export function BuildingTeamSelect(props: {
    team: Team;
    value?: BuildingTeamEntity;
    onChange: (value?: BuildingTeamEntity) => void;
    filter?: (value: BuildingTeamEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<BuildingTeamEntity>>;
    className?: string;
}) {
    return (
        <TeamEntitySelect<BuildingTeamEntity>
            entityType="buildings"
            emptyLabel="Žádná budova"
            {...props}
        />
    );
}

export function BuildingUpgradeSelect(props: {
    value?: BuildingUpgradeEntity;
    onChange: (value?: BuildingUpgradeEntity) => void;
    filter?: (value: BuildingUpgradeEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<BuildingUpgradeEntity>>;
    className?: string;
}) {
    return (
        <EntitySelect<BuildingUpgradeEntity>
            entityType="building_upgrades"
            emptyLabel="Žádné vylepšení"
            {...props}
        />
    );
}

export function BuildingUpgradeTeamSelect(props: {
    team: Team;
    value?: BuildingUpgradeTeamEntity;
    onChange: (value?: BuildingUpgradeTeamEntity) => void;
    filter?: (value: BuildingUpgradeTeamEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<BuildingUpgradeTeamEntity>>;
    className?: string;
}) {
    return (
        <TeamEntitySelect<BuildingUpgradeTeamEntity>
            entityType="building_upgrades"
            emptyLabel="Žádné vylepšení"
            {...props}
        />
    );
}

export function TeamAttributeSelect(props: {
    value?: TeamAttributeEntity;
    onChange: (value?: TeamAttributeEntity) => void;
    filter?: (value: TeamAttributeEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<TeamAttributeEntity>>;
    className?: string;
}) {
    return (
        <EntitySelect<TeamAttributeEntity>
            entityType="team_attributes"
            emptyLabel="Žádná vlastnost"
            {...props}
        />
    );
}

export function TeamAttributeTeamSelect(props: {
    team: Team;
    value?: TeamAttributeTeamEntity;
    onChange: (value?: TeamAttributeTeamEntity) => void;
    filter?: (value: TeamAttributeTeamEntity) => boolean;
    sortBy?: _.Many<_.ListIteratee<TeamAttributeTeamEntity>>;
    className?: string;
}) {
    return (
        <TeamEntitySelect<TeamAttributeTeamEntity>
            entityType="team_attributes"
            emptyLabel="Žádná vlastnost"
            {...props}
        />
    );
}
