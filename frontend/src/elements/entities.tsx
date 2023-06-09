import _ from "lodash";
import useSWR from "swr";
import useSWRImmutable from "swr/immutable";
import {
    Decimal,
    EntityBase,
    ResourceTeamEntity,
    Team,
    TechTeamEntity,
    VyrobaTeamEntity,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { fetcher } from "../utils/axios";

export const urlEntityAtom = stringAtomWithHash("entity");

export function useEntities<T>(entityType?: string) {
    return useSWRImmutable<Record<string, T & EntityBase>>(
        () => (entityType ? `game/entities/${entityType}` : "game/entities"),
        fetcher
    );
}

export function useTeamWork(teamId: string | undefined) {
    const { data, error } = useSWR<{ work: Decimal }>(
        () => (teamId ? `game/teams/${teamId}/work` : null),
        fetcher
    );
    return {
        teamWork: data?.work,
        error,
    };
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
