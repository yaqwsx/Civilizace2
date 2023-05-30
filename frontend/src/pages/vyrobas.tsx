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
import { useAtom, useSetAtom } from "jotai";
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
import { useHideMenu } from "./atoms";
import { produce } from "immer";
import { stringAtomWithHash } from "../utils/atoms";

export const urlVyrobaActionAtom = stringAtomWithHash("vyrobaAction");

export function VyrobaMenu() {
    return null;
}

export function Vyroba() {
    useHideMenu();

    const { team, setTeam, loading, error } = useTeamFromUrl();
    const setVyrobaId = useSetAtom(urlEntityAtom);
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
        setVyrobaId(RESET);
    };

    return (
        <>
            <h1>
                Zadat {vyrobaAction == "storage" ? "výběr ze skladu" : "výrobu"}
                {team ? ` pro tým ${team.name}` : null}
            </h1>
            <FormRow label="Vyber tým:">
                <TeamSelector onChange={handleTeamChange} activeId={team?.id} />
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
        setVyrobaId(event.target.value || RESET);
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
                    onReset={() => setVyrobaId(RESET)}
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

type PerformVyrobaProps = {
    vyroba: TeamEntityVyroba;
    resources: Record<string, TeamEntityResource>;
    team: Team;
    onReset: () => void;
};
function PerformVyroba(props: PerformVyrobaProps) {
    const { data: entities, error: eError } = useEntities<EntityResource>();
    const { data: tiles, error: tError } = useSWR<any[]>("/game/map", fetcher);

    const [amount, setAmount] = useState<number>(1);
    const [tile, setTile] = useState<string | undefined>(undefined);
    const [plunder, setPlunder] = useState(false);

    const vyroba = props.vyroba;

    useEffect(() => {
        if (!tiles || tile || !vyroba || !vyroba?.allowedTiles) return;
        console.log(vyroba);
        let homeTile = tiles.find((t) => t?.homeTeam === props.team.id);
        setTile(homeTile.entity);
        return;
        // if (!homeTile)
        //     return
        // if (props.vyroba.allowedTiles.includes(homeTile.entity)) {
        //     setTile(homeTile.entity);
        //     return
        // }
        // for (let t of tiles) {
        //     if (vyroba.allowedTiles.includes(t.entity)) {
        //         setTile(t.entity);
        //         return;
        //     }
        // }
        // setTile(homeTile.entity);
    }, [tiles, props.team, vyroba]);

    if (!entities || !tiles) {
        return (
            <LoadingOrError
                loading={!entities && !eError && !tiles && !tError}
                error={eError || tError}
                message="Nepodařilo se načíst entity"
            />
        );
    }

    const handleAmountChange = (x: number) => {
        if (x < 0) setAmount(0);
        else setAmount(x);
    };

    const cost = sortCostItems(
        Object.keys(vyroba.cost).map((k) => {
            return [entities[k], vyroba.cost[k]];
        })
    );

    let sortedTiles = tiles.sort((a, b) => a.name.localeCompare(b.name));

    return (
        <PerformAction
            actionName={`Výroba ${amount}× ${vyroba.name} pro tým ${props.team.name}`}
            actionId="VyrobaAction"
            actionArgs={{
                team: props.team.id,
                vyroba: props.vyroba.id,
                count: amount,
                tile: tile,
                plunder: plunder,
            }}
            argsValid={(a) => a.tile}
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
                            <option value="">Pole nevybráno</option>
                            {sortedTiles
                                // .filter((t) =>
                                //     vyroba.allowedTiles.includes(t.entity)
                                // )
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
                    <FormRow label="Chcete pole drancovat? (+50%)">
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
    const setVyrobaAction = useSetAtom(urlVyrobaActionAtom);

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
                        actionId="WithdrawAction"
                        actionArgs={{
                            team: props.team.id,
                            resources: toWithdraw,
                        }}
                        onFinish={() => {
                            mutate();
                            setSubmitting(false);
                            setToWithdraw({});
                            setVyrobaAction(RESET);
                        }}
                        onBack={() => setSubmitting(false)}
                    />
                </Dialog>
            )}
        </>
    );
}
