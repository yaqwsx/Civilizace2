import useSWR from "swr";
import {
    BuildingTeamEntity,
    BuildingUpgradeTeamEntity,
    Decimal,
    EntityId,
    FeedingRequirements,
    MapTileTeamEntity,
    ResourceId,
    ResourceTeamEntity,
    SpecialResources,
    Sticker,
    Task,
    Team,
    TeamAnnouncement,
    TeamArmy,
    TeamAttributeTeamEntity,
    TeamDashboard,
    TechId,
    TechOrgTeamEntity,
    TechTeamEntity,
    VyrobaId,
    VyrobaTeamEntity,
} from "../types";
import axiosService, { fetcher } from "../utils/axios";

function useTeamView<T>(view: string, teamId: string | undefined) {
    return useSWR<T>(
        () => (teamId ? `game/teams/${teamId}/${view}` : null),
        fetcher
    );
}

export function useTeamEntities<T>(entityType: string, team: Team | undefined) {
    return useTeamView<Record<EntityId, T>>(entityType, team?.id);
}

export function useTeamResources(team: Team | undefined) {
    return useTeamEntities<ResourceTeamEntity>("resources", team);
}
export function useTeamVyrobas(team: Team | undefined) {
    return useTeamEntities<VyrobaTeamEntity>("vyrobas", team);
}
export function useTeamBuildings(team: Team | undefined) {
    return useTeamEntities<BuildingTeamEntity>("buildings", team);
}
export function useTeamBuildingUpgrades(team: Team | undefined) {
    return useTeamEntities<BuildingUpgradeTeamEntity>(
        "building_upgrades",
        team
    );
}
export function useTeamTeamAttributes(team: Team | undefined) {
    return useTeamEntities<TeamAttributeTeamEntity>("attributes", team);
}

export function useTeamTechs(team: Team | undefined) {
    return useTeamEntities<TechTeamEntity>("techs", team);
}
export function useTeamOrgTechs(team: Team | undefined) {
    return useTeamEntities<TechOrgTeamEntity>("techs", team);
}

export function useTeamTasks(team: Team | undefined) {
    return useTeamView<Record<string, Task>>("tasks", team?.id);
}

export function useTeamTiles(team: Team | undefined) {
    return useTeamEntities<MapTileTeamEntity>("tiles", team);
}

export function useTeamSpecialResources(teamId: string | undefined) {
    return useTeamView<SpecialResources>("special_resources", teamId);
}

export function changeTeamTask(
    team: Team,
    newTask: { tech: TechId; newTask: string | null }
) {
    return axiosService.post<{}>(`/game/teams/${team.id}/changetask/`, newTask);
}

export function useTeamDashboard(teamId: string | undefined) {
    return useTeamView<TeamDashboard>("dashboard", teamId);
}

export function useTeamAnnouncements(teamId: string | undefined) {
    return useTeamView<TeamAnnouncement[]>("announcements", teamId);
}

export function useTeamArmies(team: Team | undefined) {
    return useTeamView<Record<number, TeamArmy>>("armies", team?.id);
}

export function useTeamStickers(teamId: string | undefined) {
    return useTeamView<Sticker[]>("stickers", teamId);
}

export function useTeamProductions(team: Team | undefined) {
    return useTeamView<Record<ResourceId, Decimal>>("productions", team?.id);
}
export function useTeamStorage(team: Team | undefined) {
    return useTeamView<Record<ResourceId, Decimal>>("storage", team?.id);
}
export function useTeamEmployees(team: Team | undefined) {
    return useTeamView<Record<VyrobaId, number>>("employees", team?.id);
}

export function useTeamFeeding(team: Team | undefined) {
    return useTeamView<FeedingRequirements>("feeding", team?.id);
}
