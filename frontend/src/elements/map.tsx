import useSWR from "swr";
import { classNames, LoadingOrError } from ".";
import { EntityTeamAttribute, Team } from "../types";
import { fetcher } from "../utils/axios";
import { useEntities } from "./entities";

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
            <option>Žádné políčko</option>
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
    value?: any;
    onChange: (tile: any) => void;
    className?: string;
}) {
    const { data: tiles, error } = useSWR<Record<string, any>>(
        `game/teams/${props.team.id}/tiles`,
        fetcher
    );

    if (!tiles) {
        return (
            <LoadingOrError error={error} message="Nemůžu načíst pole mapy" />
        );
    }

    const sortedTiles = Object.values(tiles).sort((a, b) =>
        a.entity.name.localeCompare(b.entity.name)
    );

    let className = classNames("select field", props.className);
    return (
        <select
            className={className}
            value={props?.value?.entity.id}
            onChange={(e) => props.onChange(tiles[e.target.value])}
        >
            <option>Žádné políčko</option>
            {sortedTiles.map((t: any) => (
                <option key={t.entity.id} value={t.entity.id}>
                    {t.entity.name}
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
            <option>Žádná budova</option>
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

export function TeamAttributeSelect(props: {
    allowed?: string[];
    value: any;
    onChange: (value: any) => void;
    className?: any;
}) {
    const { data: attributes, error } =
        useEntities<EntityTeamAttribute>("team_attributes");

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
