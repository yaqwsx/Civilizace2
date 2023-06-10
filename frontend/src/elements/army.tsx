import { useEffect } from "react";
import useSWR from "swr";
import { LoadingOrError } from ".";
import { Army, ArmyGoal, Team } from "../types";
import { fetcher } from "../utils/axios";
import _ from "lodash";

export function ArmySelectBox(props: {
    team: Team;
    value?: Army;
    onChange: (army: Army) => void;
}) {
    const { data: armies, error: armyError } = useSWR<Record<number, Army>>(
        `game/teams/${props.team.id}/armies`,
        fetcher
    );

    useEffect(() => {
        if (!props.value && armies) {
            props.onChange(Object.values(armies)[0]);
        }
    }, [armies, props.value]);

    if (!armies) {
        return <LoadingOrError error={armyError} message="Něco se pokazilo" />;
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
            return "";
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
