import { classNames, LoadingOrError } from ".";
import { MapTileTeamEntity, Team, TeamAttributeEntity } from "../types";
import { useEntities, useTeamEntities } from "./entities";

export function TileSelect(props: {
    value?: any;
    onChange: (tile: any) => void;
    className?: string;
}) {
    const { data: tiles, error } = useEntities<any>("tiles");

    if (!tiles || error) {
        return (
            <LoadingOrError error={error} message="Nemůžu načíst dlaždice" />
        );
    }

    const sortedTiles = Object.values(tiles).sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    let className = classNames("select", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) => props.onChange(tiles[e.target.value])}
        >
            <option value="">Žádné políčko</option>
            {sortedTiles.map((t: any) => (
                <option key={t.id} value={t.id}>
                    {t.name}
                </option>
            ))}
        </select>
    );
}

export function TeamTileSelect(props: {
    team: Team;
    value?: MapTileTeamEntity;
    onChange: (tile?: MapTileTeamEntity) => void;
    className?: string;
}) {
    const { data: tiles, error } = useTeamEntities<MapTileTeamEntity>(
        "tiles",
        props.team
    );

    if (!tiles) {
        return (
            <LoadingOrError error={error} message="Nemůžu načíst pole mapy" />
        );
    }

    const sortedTiles = Object.values(tiles).sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    let className = classNames("select field", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) => props.onChange(tiles[e.target.value])}
        >
            <option value="">Žádné políčko</option>
            {sortedTiles.map((t) => (
                <option key={t.id} value={t.id}>
                    {t.name}
                </option>
            ))}
        </select>
    );
}

export function BuildingSelect(props: {
    allowed?: string[] | Record<string, any>;
    value: any;
    onChange: (value: any) => void;
    className?: any;
}) {
    const { data: buildings, error } = useEntities<any>("buildings");

    if (!buildings) {
        return <LoadingOrError error={error} message="Nemůžu načíst budovy" />;
    }

    let className = classNames("select field", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) => props.onChange(buildings[e.target.value])}
        >
            <option value="">Žádná budova</option>
            {Object.values(buildings)
                .filter(
                    (b) =>
                        !props.allowed ||
                        b?.id in props.allowed ||
                        (props.allowed?.includes &&
                            props.allowed.includes(b?.id))
                )
                .map((t: any) => (
                    <option key={t.id} value={t.id}>
                        {t.name}
                    </option>
                ))}
        </select>
    );
}

export function BuildingUpgradeSelect(props: {
    allowed?: string[] | Record<string, any>;
    value: any;
    onChange: (value: any) => void;
    className?: any;
}) {
    const { data: upgrades, error } = useEntities<any>("building_upgrades");

    if (!upgrades) {
        return (
            <LoadingOrError
                error={error}
                message="Nemůžu načíst vylepšení budov"
            />
        );
    }

    let className = classNames("select field", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) => props.onChange(upgrades[e.target.value])}
        >
            <option value="">Žádné vylepšení</option>
            {Object.values(upgrades)
                .filter(
                    (u) =>
                        !props.allowed ||
                        u?.id in props.allowed ||
                        (props.allowed?.includes &&
                            props.allowed.includes(u?.id))
                )
                .map((u: any) => (
                    <option key={u.id} value={u.id}>
                        {u.name}
                    </option>
                ))}
        </select>
    );
}

export function TeamAttributeSelect(props: {
    allowed?: string[];
    value: any;
    onChange: (value: any) => void;
    className?: any;
}) {
    const { data: attributes, error } =
        useEntities<TeamAttributeEntity>("team_attributes");

    if (!attributes) {
        return (
            <LoadingOrError
                error={error}
                message="Nemůžu načíst týmové vlastnosti"
            />
        );
    }

    const className = classNames("select field", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) =>
                props.onChange(
                    e.target.value ? attributes[e.target.value] : null
                )
            }
        >
            <option value="">Žádná vlastnost</option>
            {Object.entries(attributes)
                .filter(
                    ([key]) =>
                        !props.allowed ||
                        key in props.allowed ||
                        (props.allowed?.includes && props.allowed.includes(key))
                )
                .map(([key, attribute]) => (
                    <option key={key} value={key}>
                        {attribute.name}
                    </option>
                ))}
        </select>
    );
}
