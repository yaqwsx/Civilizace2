import classNames from "classnames";
import useSWR from "swr";
import {
    FormRow,
    InlineSpinner,
    ComponentError,
    SpinboxInput,
    Button,
    Dialog,
    LoadingOrError,
} from "../elements";
import {
    useTeams,
    useTeamFromUrl,
    TeamSelector,
    TeamRowIndicator,
} from "../elements/team";
import { Team, EntityVyroba, EntityResource } from "../types";
import { useAtom } from "jotai";
import { atomWithHash, RESET } from "jotai/utils";
import { data } from "autoprefixer";
import {
    EntityTag,
    urlEntityAtom,
    useResources,
    useTeamResources,
    useTeamVyrobas,
} from "../elements/entities";
import { ChangeEvent, useState } from "react";
import { PerformAction } from "../elements/action";
import { fetcher } from "../utils/axios";
import _ from "lodash";

export const urlVyrobaActionAtom = atomWithHash<string | undefined>(
    "vyrobaAction",
    undefined,
    {
        serialize: (x) => (x ? x : ""),
        deserialize: (x) => (x ? x : undefined),
    }
);

export function VyrobaMenu() {
    return null;
}

export function Vyroba() {
    const { team, setTeam, loading, error } = useTeamFromUrl();
    const [vyrobaId, setVyrobaId] = useAtom(urlEntityAtom);
    const [vyrobaAction, setVyrobaAction] = useAtom(urlVyrobaActionAtom);

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

    const handleTeamChange = (t?: Team) => {
        setTeam(t);
        setVyrobaId(undefined);
    };

    return (
        <>
            <h1>
                Zadat {vyrobaAction == "storage" ? "výběr ze skladu" : "výrobu"}
                {team ? ` pro tým ${team.name}` : null}
            </h1>
            <FormRow label="Vyber tým:">
                <TeamSelector onChange={handleTeamChange} active={team} />
            </FormRow>
            <TeamRowIndicator team={team} />
            <FormRow label="Vyberte akci:">
                <div className="mx-0 w-1/2 flex-initial px-1">
                    <Button
                        label="Výroba"
                        className="mx-0 w-full bg-green-600 hover:bg-green-700"
                        onClick={() => setVyrobaAction("vyroba")}
                    />
                </div>
                <div className="mx-0 w-1/2 flex-initial px-1">
                    <Button
                        label="Výběr ze skladu"
                        className="w-full"
                        onClick={() => setVyrobaAction("storage")}
                    />
                </div>
            </FormRow>
            {team && vyrobaAction === "vyroba" && <SelectVyroba team={team} />}
            {team && vyrobaAction === "storage" && (
                <WithdrawStorage team={team} />
            )}
        </>
    );
}

type SelectVyrobaProps = {
    team: Team;
    active?: EntityVyroba;
    onChange?: (selectedVyroba: EntityVyroba) => void;
};
function SelectVyroba(props: SelectVyrobaProps) {
    const {
        vyrobas,
        loading: vLoading,
        error: vError,
    } = useTeamVyrobas(props.team);
    const {
        resources,
        loading: rLoading,
        error: rError,
    } = useTeamResources(props.team);
    const [vyrobaId, setVyrobaId] = useAtom(urlEntityAtom);

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
        );
    let team = props.team;
    let vyroba = vyrobaId ? vyrobas[vyrobaId] : null;

    if (vyrobaId && !(vyrobaId in vyrobas)) setVyrobaId(RESET); // When the current entity doesn't match, clear it

    const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
        setVyrobaId(event.target.value);
    };

    let vyrobasArray = Object.values(vyrobas);
    vyrobasArray.sort((a, b) => (a.name > b.name ? 1 : -1));

    return (
        <>
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
            {vyroba ? (
                <PerformVyroba
                    vyroba={vyroba}
                    team={team}
                    resources={resources}
                />
            ) : null}
        </>
    );
}

function sortCostItems(entries: [EntityResource, number][]) {
    return entries;
}

type PerformVyrobaProps = {
    vyroba: EntityVyroba;
    resources: Record<string, EntityResource>;
    team: Team;
};
function PerformVyroba(props: PerformVyrobaProps) {
    const [amount, setAmount] = useState<number>(1);

    const vyroba = props.vyroba;

    const handleAmountChange = (x: number) => {
        if (x < 0) setAmount(0);
        else setAmount(x);
    };

    const cost = sortCostItems(
        Object.keys(vyroba.cost).map((k) => {
            return [props.resources[k], vyroba.cost[k]];
        })
    );

    return (
        <>
            <FormRow label="Zadejte počet výrob:">
                <SpinboxInput value={amount} onChange={handleAmountChange} />
            </FormRow>
            <h2>
                {amount}× {vyroba.name} → {amount * vyroba.reward[1]}×{" "}
                {props.resources[vyroba.reward[0]].name}
            </h2>
            {
                // cost.map(([resource, rAmount]) => {
                //     <FormRow label={`${resource.name} (potřeba ${amount * rAmount}×)`}>
                //     </FormRow>
                // })
            }
        </>
    );
}

function WithdrawStorage(props: { team: Team }) {
    const [submitting, setSubmitting] = useState(false);
    const {
        data: storage,
        error,
        mutate,
    } = useSWR<any>(`game/teams/${props.team.id}/storage`, fetcher);
    const [toWithdraw, setToWithdraw] = useState<any>({});

    if (!storage)
        return (
            <LoadingOrError
                loading={!storage && !error}
                error={error}
                message="Něco se pokazilo"
            />
        );

    let isEmpty = Object.keys(storage).length === 0;

    return (
        <>
            <h2>Zadejte kolik vybrat ze skladu</h2>

            {Object.entries(storage).map(([r, maxV]: any) => (
                <FormRow
                    label={
                        <>
                            <EntityTag id={r} /> (max {maxV}):{" "}
                        </>
                    }
                    key={r}
                >
                    <SpinboxInput
                        value={_.get(toWithdraw, r, 0)}
                        onChange={(v) => {
                            if (v < 0) v = 0;
                            if (v > maxV) v = maxV;
                            let newW = Object.create(toWithdraw);
                            newW[r] = v;
                            setToWithdraw(newW);
                        }}
                    />
                </FormRow>
            ))}

            <Button
                label={!isEmpty ? "Vybrat" : "Tým nemá ve skladu nic"}
                className="w-full"
                onClick={() => setSubmitting(true)}
                disabled={isEmpty}
            />
            {submitting && (
                <Dialog onClose={() => setSubmitting(false)}>
                    <PerformAction
                        actionName={`Výběr ze skladu pro tým ${props.team.name}`}
                        actionId="ActionWithdraw"
                        actionArgs={{
                            team: props.team.id,
                            resources: toWithdraw,
                        }}
                        onFinish={() => {
                            mutate();
                            setSubmitting(false);
                        }}
                        onBack={() => setSubmitting(false)}
                    />
                </Dialog>
            )}
        </>
    );
}
