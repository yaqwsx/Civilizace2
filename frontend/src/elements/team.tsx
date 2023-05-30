import useSWR from "swr";
import useSWRImmutable from "swr/immutable";
import { Team } from "../types";
import { fetcher } from "../utils/axios";
import { useAtom } from "jotai";
import { RESET, atomWithHash } from "jotai/utils";
import classNames from "classnames";
import { InlineSpinner, ComponentError } from ".";

const urlTeamAtom = atomWithHash<string | null>("team", null);

export function useTeams() {
    const { data, error } = useSWRImmutable<Team[]>(() => "/teams/", fetcher);
    return {
        teams: data,
        loading: !error && !data,
        error: error,
    };
}

export function useTeam(teamId?: string) {
    const { data, error } = useSWRImmutable<Team>(
        () => (teamId ? `/teams/${teamId}` : null),
        fetcher
    );
    return {
        team: data,
        loading: !error && !data,
        error: error,
    };
}

export function useTeamIdFromUrl() {
    return useAtom(urlTeamAtom);
}

export function useTeamFromUrl() {
    const [teamId, setTeamId] = useTeamIdFromUrl();
    const { teams, loading, error } = useTeams();

    let team: Team | undefined = undefined;
    if (!loading && !error && teams && teamId) {
        team = teams.find((t) => t.id === teamId);
    }
    let combinedError = undefined;
    if (error) {
        combinedError = error;
    } else if (loading) {
        combinedError = new Error(`Could not load teams`);
    } else if (!team && teamId) {
        combinedError = new Error(`No such team ${teamId}`);
    }

    return {
        team: team,
        setTeam: (t?: Team) => setTeamId(t?.id ?? RESET),
        loading: loading,
        error: combinedError,
        allTeams: teams,
    };
}

type TeamSelectorProps = {
    activeId?: string;
    onChange?: (selectedTeam?: Team) => void;
    onError?: (message: string) => void;
    allowNull?: boolean;
    ignoredTeam?: Team;
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
                <TeamSelectorImpl
                    {...props}
                    teams={teams.filter((t) => t !== props.ignoredTeam)}
                />
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
            {!props.allowNull || (
                <button
                    className={classNames(
                        "rounded-md",
                        "m-2",
                        "shadow-lg",
                        "bg-transparent",
                        "flex-auto",
                        {
                            "scale-110 border-4 border-black font-bold":
                                !props.activeId,
                        }
                    )}
                    style={{ width: "70px", height: "70px" }}
                    onClick={() => {
                        if (props.onChange) props.onChange(undefined);
                    }}
                >
                    Nikdo
                </button>
            )}
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
                            props.activeId === team.id,
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

export function TeamRowIndicator(props: { team?: Team }) {
    if (!props.team) return null;
    let className = classNames(
        "w-full",
        "rounded",
        "h-4",
        "my-4",
        `bg-${props.team.color}`
    );
    return <div className={className} />;
}
