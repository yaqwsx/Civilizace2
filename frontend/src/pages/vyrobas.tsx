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
import {
    Team,
    TeamEntityVyroba,
    EntityResource,
    Entity,
    TeamEntityResource,
} from "../types";
import { useAtom } from "jotai";
import { atomWithHash, RESET } from "jotai/utils";
import { data } from "autoprefixer";
import {
    EntityTag,
    urlEntityAtom,
    useEntities,
    useResources,
    useTeamEntity,
    useTeamResources,
    useTeamVyrobas,
} from "../elements/entities";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { PerformAction } from "../elements/action";
import { fetcher } from "../utils/axios";
import _ from "lodash";
import { ARMY_GOALS } from "./map";
import { useHideMenu } from "./atoms";
import { produce } from "immer";

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
    useHideMenu();

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
    active?: TeamEntityVyroba;
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

    const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
        setVyrobaId(event.target.value);
    };

    let vyrobasArray = Object.values(vyrobas);
    vyrobasArray.sort((a, b) => (a.name > b.name ? 1 : -1));

    return (
        <>
            <h2>Vyberte výrobu</h2>
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
                    onReset={() => setVyrobaId(undefined)}
                />
            ) : null}
        </>
    );
}

function sortCostItems(entries: [EntityResource, number][]) {
    return entries.sort((x, y) => {
        let a = x[0];
        let b = y[0];

        if (a.id == "res-prace") return -1;
        if (b.id == "res-prace") return 1;
        if (a.id == "res-obyvatel") return -1;
        if (b.id == "res-obyvatel") return 1;
        if (isGeneric(a) && isGeneric(b)) return 0;
        if (isGeneric(a)) return -1;
        if (isGeneric(b)) return 1;
        return 0;
    });
}

function isGeneric(entity: Entity) {
    return entity.id.startsWith("mge-") || entity.id.startsWith("pge-");
}

function isProduction(e: EntityResource) {
    return e.id.startsWith("pro-") || e.id.startsWith("pge-");
}

function isConcretization(what: EntityResource, generic: EntityResource) {
    if (!what || !generic || !what.typ || !generic.typ) return false;

    return (
        what?.typ?.id == generic?.typ?.id &&
        what?.typ?.level >= generic?.typ?.level &&
        isProduction(what) == isProduction(generic)
    );
}

function computeConcretization(entities?: Record<string, EntityResource>) {
    if (!entities) return {};
    let generic = Object.values(entities).filter(isGeneric);
    let mapping: Record<string, EntityResource[]> = Object.fromEntries(
        generic.map((g) => [g.id, []])
    );
    Object.values(entities).forEach((e) => {
        if (isGeneric(e)) return;
        generic.forEach((g) => {
            if (isConcretization(e, g)) mapping[g.id].push(e);
        });
    });
    return mapping;
}

type PerformVyrobaProps = {
    vyroba: TeamEntityVyroba;
    resources: Record<string, TeamEntityResource>;
    team: Team;
    onReset: () => void;
};
function PerformVyroba(props: PerformVyrobaProps) {
    const { data: entities, error: eError } = useEntities<EntityResource>();
    const { data: tiles, error: tError } = useSWR<any[]>("/game/map", fetcher);
    const mapping = useMemo(() => computeConcretization(entities), [entities]);

    const [amount, setAmount] = useState<number>(1);
    const [tile, setTile] = useState<string | undefined>(undefined);
    const [concretization, setConcretization] = useState<
        Record<string, string>
    >({});
    const [plunder, setPlunder] = useState(false);
    const [useArmy, setUseArmy] = useState(false);
    const [equipment, setEquipment] = useState(1);
    const [goal, setGoal] = useState<any>(0);

    useEffect(() => {
        if (!tiles || tile) return;
        setTile(tiles.find((t) => t?.homeTeam === props.team.id).entity);
    }, [tiles, props.team]);

    if (!entities || !tiles) {
        return (
            <LoadingOrError
                loading={!entities && !eError && !tiles && !tError}
                error={eError || tError}
                message="Nepodařilo se načíst entity"
            />
        );
    }

    const vyroba = props.vyroba;

    const handleAmountChange = (x: number) => {
        if (x < 0) setAmount(0);
        else setAmount(x);
    };

    const cost = sortCostItems(
        Object.keys(vyroba.cost).map((k) => {
            return [entities[k], vyroba.cost[k]];
        })
    );

    return (
        <PerformAction
            team={props.team}
            actionName={`Výroba ${amount}× ${vyroba.name} pro tým ${props.team.name}`}
            actionId="ActionVyroba"
            actionArgs={{
                team: props.team.id,
                vyroba: props.vyroba.id,
                count: amount,
                tile: tile,
                plunder: plunder,
                genericsMapping: concretization,
                // TBA army
            }}
            onFinish={() => props.onReset()}
            onBack={() => props.onReset()}
            extraPreview={
                <>
                    <FormRow label="Zadejte počet výrob:">
                        <SpinboxInput
                            value={amount}
                            onChange={handleAmountChange}
                        />
                    </FormRow>
                    <FormRow label="Vyberte pole mapy pro výrobu:">
                        <select
                            className="select field"
                            value={tile}
                            onChange={(e) => setTile(e.target.value)}
                        >
                            {tiles
                                .filter((t) =>
                                    vyroba.allowedTiles.includes(t.entity)
                                )
                                .map((t) => (
                                    <option key={t.entity} value={t.entity}>
                                        {t.name}{" "}
                                        {t?.homeTeam
                                            ? `(domovské ${t.homeTeam})`
                                            : null}
                                    </option>
                                ))}
                        </select>
                    </FormRow>
                    <FormRow label="Chcete pole drancovat (+25%)?">
                        <input
                            className="checkboxinput"
                            type="checkbox"
                            checked={plunder}
                            onChange={(e) => setPlunder(e.target.checked)}
                        />
                    </FormRow>
                    <h2>
                        {amount}× {vyroba.name} → {amount * vyroba.reward[1]}×{" "}
                        <EntityTag id={vyroba.reward[0]} />
                    </h2>
                    {cost.map(([resource, rAmount]) => {
                        let available = _.get(
                            props.resources,
                            resource.id,
                            undefined
                        )?.available;
                        let error = undefined;
                        if (available !== undefined && available < rAmount)
                            error = "Nedostatek zdroje";
                        let input = (
                            <select className="field select w-full">
                                <option>
                                    {resource.name}{" "}
                                    {available && `(${available}×)`}
                                </option>
                            </select>
                        );
                        if (isProduction(resource) && isGeneric(resource)) {
                            let options = mapping[resource.id];
                            let value = _.get(concretization, resource.id, "");

                            let available = _.get(
                                props.resources,
                                value,
                                undefined
                            )?.available;
                            if (available !== undefined && available < rAmount)
                                error = "Nedostatek zdroje";

                            input = (
                                <select
                                    className="field select w-full bg-blue-300"
                                    value={value}
                                    onChange={(e) => {
                                        let newV = e.target.value;
                                        let newC =
                                            Object.create(concretization);
                                        newC[resource.id] = newV;
                                        setConcretization(newC);
                                        console.log("Y", resource.id, newC);
                                    }}
                                >
                                    <option>Vyberte konkretizaci</option>
                                    {options.map((o) => {
                                        let available = _.get(
                                            props.resources,
                                            o.id,
                                            undefined
                                        )?.available;
                                        return (
                                            <option key={o.id} value={o.id}>
                                                {o.name}{" "}
                                                {available && `(${available}×)`}
                                            </option>
                                        );
                                    })}
                                </select>
                            );
                        }
                        return (
                            <FormRow
                                key={resource.id}
                                label={`Je třeba ${amount * rAmount}× ${
                                    resource.name
                                } a realizuje se jako: `}
                                error={error}
                            >
                                {input}
                            </FormRow>
                        );
                    })}
                    {/* <h2>Armádní posila</h2>
                    <FormRow label="Přejete si poslat armádu?">
                        <input
                            className="checkboxinput"
                            type="checkbox"
                            checked={useArmy}
                            onChange={(e) => setUseArmy(e.target.checked)}
                        />
                    </FormRow>
                    {useArmy && (
                        <>
                            <FormRow label="Vyberte armádu:">
                                <select className="field select">
                                    <option>
                                        Armáda A (síla 10) stojí na poli 28
                                    </option>
                                    <option>
                                        Armáda B (síla 10) stojí na poli 12
                                    </option>
                                    <option>
                                        Armáda C (síla 10) stojí na poli 4
                                    </option>
                                </select>
                            </FormRow>
                            <FormRow label="Mód:">
                                <select
                                    className="select"
                                    value={goal}
                                    onChange={(e) =>
                                        setGoal(parseInt(e.target.value))
                                    }
                                >
                                    {Object.entries(ARMY_GOALS).map(
                                        ([k, v]) => {
                                            if (k == "2")
                                                // Zásobování
                                                return null;
                                            return (
                                                <option key={k} value={k}>
                                                    {v}
                                                </option>
                                            );
                                        }
                                    )}
                                </select>
                            </FormRow>
                            <FormRow label="Jakou bude mít výzbroj?">
                                <SpinboxInput
                                    value={equipment}
                                    onChange={setEquipment}
                                />
                            </FormRow>
                        </>
                    )} */}
                </>
            }
        />
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
                            <span
                                className="cursor-pointer"
                                onClick={() => {
                                    setToWithdraw(
                                        produce(toWithdraw, (next: any) => {
                                            next[r] = maxV;
                                        })
                                    );
                                }}
                            >
                                <EntityTag id={r} /> (max {maxV}):{" "}
                            </span>
                        </>
                    }
                    key={r}
                >
                    <SpinboxInput
                        value={_.get(toWithdraw, r, 0)}
                        onChange={(v) => {
                            setToWithdraw(
                                produce(toWithdraw, (next: any) => {
                                    if (v < 0) v = 0;
                                    if (v > maxV) v = maxV;
                                    next[r] = v;
                                })
                            );
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
