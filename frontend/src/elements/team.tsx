import useSWR from "swr";
import { Team } from "../types";
import { fetcher } from "../utils/axios";
import { useAtom } from "jotai";
import { atomWithHash } from "jotai/utils";
import classNames from "classnames";
import { InlineSpinner, ComponentError } from ".";

const urlTeamAtom = atomWithHash<string | undefined>("team", undefined,
    {
        serialize: x => x ? x : "",
        deserialize: x => x ? x : undefined
    });

export function useTeams() {
    const { data, error } = useSWR<Team[]>("/team/", fetcher);
    return {
        teams: data,
        loading: !error && !data,
        error: error,
    };
}

export function useTeamFromUrl() {
    const [teamId, setTeamId] = useAtom(urlTeamAtom);
    const { teams, loading, error } = useTeams();

    let team = undefined;
    if (!loading && !error && teams) {
        for (const i in teams) {
            if (teams[i].id === teamId) {
                team = teams[i];
                break;
            }
        }
    }
    let combinedError = undefined;
    if (error) combinedError = error;
    else if (!team && teamId)
        combinedError = new Error(`No such team ${teamId}`);

    return {
        team: team,
        setTeam: (t?: Team) => setTeamId(t?.id),
        loading: loading,
        error: combinedError,
    };
}

type TeamSelectorProps = {
    active?: Team;
    onChange?: (selectedTeam: Team) => void;
    onError?: (message: string) => void;
};
export function TeamSelector(props: TeamSelectorProps) {
    const { teams, loading, error } = useTeams();
    if (error && props.onError) {
        props.onError(
            "Nemůžu načíst týmy ze serveru. Zkouším znovu...\n" +
                error.toString()
        );
    }

    if (loading) {
        return <InlineSpinner />;
    }

    return (
        <div className="flex w-full flex-wrap">
            {error ? (
                <ComponentError>
                    <p>Nemůžu načíst týmy ze serveru. Zkouším znovu...</p>
                    <p>{error.toString()}</p>
                </ComponentError>
            ) : teams ? (
                <TeamSelectorImpl {...props} teams={teams} />
            ) : (
                <InlineSpinner />
            )}
        </div>
    );
}

type TeamSelectorImplProps = TeamSelectorProps & {
    teams: Team[];
};
function TeamSelectorImpl(props: TeamSelectorImplProps) {
    return (
        <>
            {props.teams.map((team) => {
                let handleClick = () => {
                    if (props.onChange) props.onChange(team);
                };
                let className = classNames(
                    "rounded-md",
                    "m-2",
                    "shadow-lg",
                    `bg-${team.color}`,
                    "flex-auto",
                    {
                        "border-4 border-black scale-110 font-bold":
                            props?.active?.id === team.id,
                    }
                );
                return (
                    <button
                        key={team.id}
                        className={className}
                        style={{ width: "70px", height: "70px" }}
                        onClick={handleClick}
                    >
                        {team.name}
                    </button>
                );
            })}
        </>
    );
}

export function TeamRowIndicator(props: {team?: Team}) {
    if (!props.team)
        return null;
    let className = classNames("w-full", "rounded", "h-4", `bg-${props.team.color}`)
    return <div className={className}/>
}
