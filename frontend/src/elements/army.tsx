import { useEffect } from "react";
import useSWR from "swr";
import { LoadingOrError } from ".";
import { Team } from "../types";
import { fetcher } from "../utils/axios";

export function ArmySelectBox(props: {
    team: Team;
    value: any;
    onChange: (army: any) => void;
}) {
    const { data: armies, error: armyError } = useSWR<Record<number, any>>(
        `game/teams/${props.team.id}/armies`,
        fetcher
    );

    useEffect(() => {
        if (!props.value && armies) props.onChange(Object.values(armies)[0]);
    }, [armies, props.value]);

    if (!armies) {
        return (
            <LoadingOrError
                loading={!armies && !armyError}
                error={armyError}
                message="Něco se pokazilo"
            />
        );
    }

    let handleChange = (id: any) => {
        props.onChange(armies[id]);
    };
    return (
        <select
            className="field select"
            onChange={(e) => handleChange(e.target.value)}
            value={props?.value?.index}
        >
            {Object.values(armies).map((a) => (
                <option key={a.index} value={a.index}>
                    Armáda {a.name} {"✱".repeat(a.level)}
                </option>
            ))}
        </select>
    );
}

export const ARMY_GOALS = {
    0: "Okupovat",
    1: "Eliminovat",
    2: "Zásobování",
    3: "Nahradit",
};

export function ArmyGoalSelect(props: {
    value: number;
    onChange: (v: number) => void;
}) {
    useEffect(() => {
        if (!props.value)
            props.onChange(0);
    }, [props.value]);

    return (
        <select
            className="field select"
            onChange={(e) => props.onChange(parseInt(e.target.value))}
            value={props.value}
        >
            {Object.entries(ARMY_GOALS).map(([k, v]) => {
                return (
                    <option key={k} value={k}>
                        {v}
                    </option>
                );
            })}
        </select>
    );
}
