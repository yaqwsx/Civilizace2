import useSWR, { mutate } from "swr";
import { EntityResource, Team, TeamEntityResource, TeamEntityTech } from "../types";
import { fetcher } from "../utils/axios";
import { useAtom } from "jotai";
import { atomWithHash } from "jotai/utils";
import { EntityVyroba } from "../types"

export const urlEntityAtom = atomWithHash< string | undefined>("entity",
    undefined, {
        serialize: x => x ? x : "",
        deserialize: x => x ? x : undefined
    });

export function useTeamEntity<T>(entityType: string, team?: Team) {
    const {data, error, mutate} = useSWR<Record<string, T>>(
        () => team ? `game/teams/${team.id}/${entityType}` : null,
        fetcher)
    return {
        data: data,
        loading: !error && !data && Boolean(team),
        error: error,
        mutate: mutate
    }
}

export function useEntities<T>(entityType?: string) {
    const {data, error, mutate} = useSWR<Record<string, T>>(
        () => entityType ? `game/entities/${entityType}` : `game/entities`, fetcher);
    return {
        data: data,
        loading: !error && !data,
        error: error,
        mutate: mutate
    };
}

export function useTeamVyrobas(team?: Team) {
    const {data, ...rest} = useTeamEntity< EntityVyroba >("vyrobas", team);
    return {
        vyrobas: data,
        ...rest
    };
}

export function useResources() {
    const {data, ...rest} = useEntities<EntityResource>("resources");
    return {
        resources: data,
        ...rest
    };
}


export function useTeamResources(team?: Team) {
    const {data, ...rest} = useTeamEntity<TeamEntityResource>("resources", team);
    return {
        resources: data,
        ...rest
    };
}

export function useTeamTechs(team?: Team) {
    const {data, ...rest} = useTeamEntity<TeamEntityTech>("techs", team);
    return {
        techs: data,
        ...rest
    }
}
