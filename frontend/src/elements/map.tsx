import useSWR from "swr";
import { classNames, LoadingOrError } from ".";
import { Team } from "../types";
import { fetcher } from "../utils/axios";
import { useEntities } from "./entities";

export function TileSelect(props: {
    value?: any;
    onChange: (tile: any) => void;
    className?: string;
}) {
    const { data: tiles, loading, error } = useEntities<any>("tiles");

    if (!tiles || error) {
        return (
            <LoadingOrError
                loading={loading}
                error={error}
                message="Nemůžu načíst dlaždice"
            />
        );
    }

    let className = classNames("select", props.className);
    return (
        <select
            className={className}
            value={props?.value?.id}
            onChange={(e) => props.onChange(tiles[e.target.value])}
        >
            <option>Žádné políčko</option>
            {Object.values(tiles).map((t: any) => (
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

    if (!tiles || error) {
        return (
            <LoadingOrError
                loading={!tiles && !error}
                error={error}
                message="Nemůžu načíst dlaždice"
            />
        );
    }

    let className = classNames("select field", props.className);
    return (
        <select
            className={className}
            value={props?.value?.entity.id}
            onChange={(e) => props.onChange(tiles[e.target.value])}
        >
            <option>Žádné políčko</option>
            {Object.values(tiles).map((t: any) => (
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

    if (!buildings || error) {
        return (
            <LoadingOrError
                loading={!buildings && !error}
                error={error}
                message="Nemůžu načíst budovy"
            />
        );
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
