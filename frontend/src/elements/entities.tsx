import useSWR from "swr";
import { EntityResource, Team, TeamEntityResource } from "../types";
import { fetcher } from "../utils/axios";
import { useAtom } from "jotai";
import { atomWithHash } from "jotai/utils";
import { EntityVyroba } from "../types"

export const urlEntityAtom = atomWithHash< string | undefined>("entity",
    undefined, {
        serialize: x => x ? x : "",
        deserialize: x => x ? x : undefined
    });

export function useTeamVyrobas(team?: Team) {
    const {data, error} = useSWR<Record<string, EntityVyroba>>(
        () => team ? `game/entity/${team.id}?type=vyroba` : null,
        fetcher)
    return {
        vyrobas: data,
        loading: !error && !data && team,
        error: error
    }
}

export function useResources() {
    const {data, error} = useSWR<Record<string, EntityResource>>(
        "game/entity?type=resource", fetcher)
    return {
        resources: data,
        loading: !error && !data,
        error: error
    }
}

export function useTeamResources(team?: Team) {
    const {data, error} = useSWR<Record<string, TeamEntityResource>>(
        () => team ? `game/entity/${team.id}?type=resource` : null, fetcher)
    return {
        resources: data,
        loading: !error && !data && team,
        error: error
    }
}
