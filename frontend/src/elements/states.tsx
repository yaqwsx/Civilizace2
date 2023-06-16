import useSWR, { SWRConfiguration } from "swr";
import { ArmyState, MapTileViewState } from "../types";
import { fetcher } from "../utils/axios";

export function useMapTileStates(
    config?: SWRConfiguration<MapTileViewState[]>
) {
    const { data, ...rest } = useSWR<MapTileViewState[]>(
        "/game/map",
        fetcher,
        config
    );
    return { tiles: data, ...rest };
}

export function useArmyStates(config?: SWRConfiguration<ArmyState[]>) {
    const { data, ...rest } = useSWR<ArmyState[]>(
        "/game/armies",
        fetcher,
        config
    );
    return { armies: data, ...rest };
}
