import classNames from "classnames";
import useSWR from "swr";
import { FormRow, InlineSpinner, ComponentError, SpinboxInput } from "../elements";
import {
    useTeams,
    useTeamFromUrl,
    TeamSelector,
    TeamRowIndicator,
} from "../elements/team";
import { Team, EntityVyroba, EntityResource } from "../types";
import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import { data } from "autoprefixer";
import { urlEntityAtom, useResources, useTeamResources, useTeamVyrobas } from "../elements/entities";
import { ChangeEvent, useState } from "react";

export function VyrobaMenu() {
    return null;
}

export function Vyroba() {
    const { team, setTeam, loading, error } = useTeamFromUrl();
    const [vyrobaId, setVyrobaId] = useAtom(urlEntityAtom);

    if (loading) {
        return <InlineSpinner />;
    }
    if (error) {
        return (
            <ComponentError>
                <p>Nemůžu načíst týmy ze serveru. Zkouším znovu...</p>
                <p>{error.toString()}</p>
            </ComponentError>
        );
    }

    const handleTeamChange = (t: Team) => {
        console.log(t);
        setTeam(t);
        setVyrobaId(undefined);
    };

    return (
        <>
            <h2>
                Zadat výrobu
                {team ? ` pro tým ${team.name}` : null}
            </h2>
            <FormRow label="Vyber tým:">
                <TeamSelector onChange={handleTeamChange} active={team} />
            </FormRow>
            <TeamRowIndicator team={team} />
            <SelectVyroba team={team} />
        </>
    );
}

type SelectVyrobaProps = {
    team?: Team;
    active?: EntityVyroba;
    onChange?: (selectedVyroba: EntityVyroba) => void;
};
function SelectVyroba(props: SelectVyrobaProps) {
    const { vyrobas, loading: vLoading, error: vError } = useTeamVyrobas(props.team);
    const { resources, loading: rLoading, error: rError } = useTeamResources(props.team);
    const [vyrobaId, setVyrobaId] = useAtom(urlEntityAtom);

    if (!props.team)return null;
    if (vLoading || rLoading) return <InlineSpinner />;
    if (vError || !vyrobas)
        return (
            <ComponentError>
                Nemohu načíst entity týmu: {vError.toString()}
            </ComponentError>
        );
    if (rError || !resources)
        return (
            <ComponentError>
                Nemohu načíst zdroje: {rError.toString()}
            </ComponentError>
        )
    let team = props.team;
    let vyroba = vyrobaId ? vyrobas[vyrobaId] : null;

    if (vyrobaId && !(vyrobaId in vyrobas)) setVyrobaId(RESET); // When the current entity doesn't match, clear it

    const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
        setVyrobaId(event.target.value);
    };

    let vyrobasArray = Object.values(vyrobas);
    vyrobasArray.sort((a, b) => (a.name > b.name ? 1 : -1));

    return (<>
        <FormRow label="Vyber výrobu:" className="my-8">
            <select
                value={String(vyrobaId)}
                onChange={handleChange}
                className="select"
            >
                <option value={String(undefined)}>Vyber výrobu</option>
                {vyrobasArray.map((v) => {
                    return (
                        <option key={v.id} value={v.id}>
                            {v.name}
                        </option>
                    );
                })}
            </select>
        </FormRow>
        {
            vyroba
                ? <PerformVyroba
                    vyroba={vyroba}
                    team={team}
                    resources={resources}/>
                : null
        }
    </>);
}

function sortCostItems(entries: [EntityResource, number][]) {
    return entries;
}

type PerformVyrobaProps = {
    vyroba: EntityVyroba;
    resources: Record<string, EntityResource>;
    team: Team;
}
function PerformVyroba(props: PerformVyrobaProps) {
    const [amount, setAmount] = useState<number>(1);

    const vyroba = props.vyroba;

    const handleAmountChange = (x: number) => {
        if (x < 0)
            setAmount(0);
        else
            setAmount(x)
    }

    const cost = sortCostItems(Object.keys(vyroba.cost).map(k => {
        return [props.resources[k], vyroba.cost[k]];
    }))

    return (<>
        <FormRow label="Zadejte počet výrob:">
            <SpinboxInput value={amount} onChange={handleAmountChange}/>
        </FormRow>
        <h2>
            {amount}× {vyroba.name} → {amount * vyroba.reward[1]}× {props.resources[vyroba.reward[0]].name}
        </h2>
        {
            // cost.map(([resource, rAmount]) => {
            //     <FormRow label={`${resource.name} (potřeba ${amount * rAmount}×)`}>

            //     </FormRow>
            // })
        }
    </>)
}
