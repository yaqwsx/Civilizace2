import _ from "lodash";
import { useEffect } from "react";
import { LoadingOrError } from ".";
import { ArmyGoal, Team, TeamArmy } from "../types";
import { useTeamArmies } from "./team_view";

export function ArmySelectBox(props: {
    team: Team;
    value?: TeamArmy;
    onChange: (army: TeamArmy) => void;
}) {
    const { data: armies, error } = useTeamArmies(props.team);

    useEffect(() => {
        if (!props.value && armies) {
            props.onChange(Object.values(armies)[0]);
        }
    }, [armies, props.value]);

    if (!armies) {
        return <LoadingOrError error={error} message="Něco se pokazilo" />;
    }

    let handleChange = (index: number) => {
        props.onChange(armies[index]);
    };
    return (
        <select
            className="field select"
            onChange={(e) => handleChange(Number(e.target.value))}
            value={props.value?.index ?? ""}
        >
            {Object.values(armies).map((a) => (
                <option key={a.index} value={a.index}>
                    Armáda {a.name} {"✱".repeat(a.level)}
                </option>
            ))}
        </select>
    );
}

function getArmyGoalStr(goal: ArmyGoal): string {
    switch (goal) {
        case ArmyGoal.Occupy:
            return "Okupovat";
        case ArmyGoal.Eliminate:
            return "Eliminovat";
        case ArmyGoal.Supply:
            return "Zásobování";
        case ArmyGoal.Replace:
            return "Nahradit";

        default:
            const exhaustiveCheck: never = goal;
            return ""; // For invalid Enum value
    }
}

export function ArmyGoalSelect(props: {
    value: ArmyGoal;
    onChange: (v: ArmyGoal) => void;
}) {
    useEffect(() => {
        if (!props.value) props.onChange(ArmyGoal.Occupy);
    }, [props.value]);

    return (
        <select
            className="field select"
            onChange={(e) => props.onChange(_.get(ArmyGoal, e.target.value))}
            value={props.value ?? ""}
        >
            {Object.values(ArmyGoal).map((goal) => {
                return (
                    <option key={goal} value={goal}>
                        {getArmyGoalStr(goal)}
                    </option>
                );
            })}
        </select>
    );
}
