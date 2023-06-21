import _ from "lodash";
import useSWR from "swr";
import useSWRImmutable from "swr/immutable";
import {
    Decimal,
    EntityBase,
    ResourceTeamEntity,
    SpecialResources,
    Team,
    TechTeamEntity,
    VyrobaTeamEntity,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { fetcher } from "../utils/axios";

export const urlEntityAtom = stringAtomWithHash("entity");

export function useEntities<T = EntityBase>(entityType?: string) {
    return useSWRImmutable<Record<string, T & EntityBase>>(
        () => (entityType ? `game/entities/${entityType}` : "game/entities"),
        fetcher
    );
}

export function useTeamSpecialResources(teamId: string | undefined) {
    return useSWR<SpecialResources>(
        () => (teamId ? `game/teams/${teamId}/special_resources` : null),
        fetcher
    );
}

export function useTeamEntities<T>(entityType: string, team: Team | undefined) {
    return useSWR<Record<string, T>>(
        () => (team ? `game/teams/${team.id}/${entityType}` : null),
        fetcher
    );
}

export function useTeamVyrobas(team: Team | undefined) {
    const { data, ...rest } = useTeamEntities<VyrobaTeamEntity>(
        "vyrobas",
        team
    );
    return {
        vyrobas: data,
        ...rest,
    };
}

export function useTeamResources(team: Team | undefined) {
    const { data, ...rest } = useTeamEntities<ResourceTeamEntity>(
        "resources",
        team
    );
    return {
        resources: data,
        ...rest,
    };
}

export function useTeamTechs(team: Team | undefined) {
    const { data, ...rest } = useTeamEntities<TechTeamEntity>("techs", team);
    return {
        techs: data,
        ...rest,
    };
}

export function EntityTag(props: { id: string; quantity?: Decimal }) {
    const { data } = useEntities();

    const entity = !_.isNil(data) ? data[props.id] : undefined;
    const isProduction =
        String(props.id).startsWith("pro-") ||
        String(props.id).startsWith("pge-");
    const nameClassNames = isProduction ? "underline" : "";

    const iconMarkup = entity?.icon ? (
        <>
            <img
                className="mx-1 inline-block h-8 w-8 align-middle"
                src={`/assets/icons/${entity.icon}`}
            />{" "}
        </>
    ) : null;

    return (
        <span>
            {!_.isNil(props.quantity) ? `${props.quantity}× ` : null}
            {iconMarkup}
            <span className={nameClassNames}>{entity?.name || props.id}</span>
        </span>
    );
}
