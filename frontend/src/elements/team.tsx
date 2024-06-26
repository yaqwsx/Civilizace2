import classNames from "classnames";
import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import _ from "lodash";
import useSWRImmutable from "swr/immutable";
import { ComponentError, InlineSpinner } from ".";
import { Team } from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { fetcher } from "../utils/axios";

const urlTeamAtom = stringAtomWithHash("team");

export function useTeams() {
    const { data, error } = useSWRImmutable<Team[]>(() => "/teams/", fetcher);
    return {
        teams: data,
        error,
    };
}

export function useTeam(teamId?: string) {
    const { data, error } = useSWRImmutable<Team>(
        () => (teamId ? `/teams/${teamId}` : null),
        fetcher
    );
    return {
        team: data,
        error,
    };
}

export function useTeamIdFromUrl() {
    return useAtom(urlTeamAtom);
}

export function useTeamFromUrl() {
    const [teamId, setTeamId] = useTeamIdFromUrl();
    const { teams: allTeams, error } = useTeams();

    console.assert(!error, "Error loading teams:", error);

    const team = !_.isNil(teamId)
        ? allTeams?.find((t) => t.id === teamId)
        : null;

    return {
        team,
        setTeam: (t?: Team) => setTeamId(t?.id ?? RESET),
        success: !_.isUndefined(team),
        error:
            error ||
            (_.isNil(allTeams) && new Error(`Could not load teams`)) ||
            (!_.isNil(teamId) &&
                _.isNil(team) &&
                new Error(`No such team ${teamId}`)) ||
            undefined,
        allTeams,
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
    const { teams, error } = useTeams();
    if (error && props.onError) {
        props.onError("Nemůžu načíst týmy ze serveru. " + error.toString());
    }

    return (
        <div className="flex w-full flex-wrap">
            {error ? (
                <ComponentError>
                    <p>Nemůžu načíst týmy ze serveru</p>
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
