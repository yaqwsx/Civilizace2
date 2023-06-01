import _ from "lodash";
import useSWR from "swr";
import useSWRImmutable from "swr/immutable";
import {
    EntityBase,
    ResourceEntity,
    Team,
    TeamEntityResource,
    TeamEntityTech,
    TeamEntityVyroba,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { fetcher } from "../utils/axios";

export const urlEntityAtom = stringAtomWithHash("entity");

export function useEntities<T>(entityType?: string) {
    const { data, error, mutate } = useSWRImmutable<
        Record<string, T & EntityBase>
    >(
        () => (entityType ? `game/entities/${entityType}` : `game/entities`),
        fetcher
    );
    return {
        data,
        loading: !error && !data,
        error: error,
        mutate: mutate,
    };
}

export function useTeamWork(teamId?: string) {
    const { data, error } = useSWR<Record<string, number>>(
        () => (teamId ? `game/teams/${teamId}/work` : null),
        fetcher
    );
    return {
        teamWork: data ? data["work"] : null,
        error: error,
    };
}

export function useTeamEntity<T>(entityType: string, team?: Team) {
    const { data, error, mutate } = useSWR<Record<string, T>>(
        () => (team ? `game/teams/${team.id}/${entityType}` : null),
        fetcher
    );
    return {
        data: data,
        loading: !error && !data && Boolean(team),
        error: error,
        mutate: mutate,
    };
}

export function useTeamVyrobas(team?: Team) {
    const { data, ...rest } = useTeamEntity<TeamEntityVyroba>("vyrobas", team);
    return {
        vyrobas: data,
        ...rest,
    };
}

export function useTeamResources(team?: Team) {
    const { data, ...rest } = useTeamEntity<TeamEntityResource>(
        "resources",
        team
    );
    return {
        resources: data,
        ...rest,
    };
}

export function useTeamTechs(team?: Team) {
    const { data, ...rest } = useTeamEntity<TeamEntityTech>("techs", team);
    return {
        techs: data,
        ...rest,
    };
}

export function EntityTag(props: { id: string; quantity?: number }) {
    const { data } = useEntities();
    let isProduction = String(props.id).startsWith("pro-");
    let name = props.id;
    if (data && data[props.id]?.name) name = data[props.id].name;

    let icon = data && data[props.id]?.icon;

    let iconMarkup = icon ? (
        <img
            className="mx-1 inline-block h-8 w-8 align-middle"
            src={`/assets/icons/${icon}`}
        />
    ) : null;

    let nameMarkup = isProduction ? (
        <span className="underline">{name}</span>
    ) : (
        <span>{name}</span>
    );

    return (
        <span>
            {!_.isNil(props.quantity) ? `${props.quantity}× ` : null}
            {iconMarkup} {nameMarkup}
        </span>
    );
}

export function EntityMdTag({ node }: any) {
    if (node.value.length == 1) return <EntityTag id={node.value[0]} />;
    return <EntityTag id={node.value[0]} quantity={node.value[1]} />;
}
