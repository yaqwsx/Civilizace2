import { produce } from "immer";
import { useAtom, useSetAtom } from "jotai";
import { RESET } from "jotai/utils";
import _ from "lodash";
import { ChangeEvent, useEffect, useState } from "react";
import useSWR from "swr";
import {
    Button,
    ComponentError,
    Dialog,
    FormRow,
    LoadingOrError,
    SpinboxInput,
} from "../elements";
import { PerformAction } from "../elements/action";
import {
    EntityTag,
    urlEntityAtom,
    useEntities,
    useTeamResources,
    useTeamVyrobas,
} from "../elements/entities";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    Decimal,
    ResourceEntity,
    ResourceTeamEntity,
    Team,
    VyrobaTeamEntity,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";

export const urlVyrobaActionAtom = stringAtomWithHash("vyrobaAction");

export function VyrobaMenu() {
    return null;
}

export function Vyroba() {
    useHideMenu();

    const { team, setTeam, error, success } = useTeamFromUrl();
    const setVyrobaId = useSetAtom(urlEntityAtom);
    const [vyrobaAction, setVyrobaAction] = useAtom(urlVyrobaActionAtom);

    if (!success) {
        return (
            <LoadingOrError
                error={error}
                message="Nemůžu načíst týmy ze serveru."
            />
        );
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
            <TeamRowIndicator team={team ?? undefined} />
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
    active?: VyrobaTeamEntity;
};
function SelectVyroba(props: SelectVyrobaProps) {
    const { vyrobas, error: vError } = useTeamVyrobas(props.team);
    const { resources, error: rError } = useTeamResources(props.team);
    const [vyrobaId, setVyrobaId] = useAtom(urlEntityAtom);

    if (!vyrobas) {
        return (
            <LoadingOrError
                error={vError}
                message="Nemohu načíst výroby týmu."
            />
        );
    }
    if (!resources) {
        return (
            <LoadingOrError error={rError} message="Nemohu načíst zdroje." />
        );
    }
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
                    value={vyrobaId ?? ""}
                    onChange={handleChange}
                    className="select"
                >
                    <option value="">Vyber výrobu</option>
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
                    team={props.team}
                    resources={resources}
                    onReset={() => setVyrobaId(RESET)}
                />
            ) : null}
        </>
    );
}

function sortCostItems(entries: [ResourceEntity, Decimal][]) {
    const sortIndex = (res: ResourceEntity) => {
        if (res.id === "res-prace") return 0;
        if (res.id === "res-obyvatel") return 1;
        if (isGeneric(res) && isProduction(res)) return 2;
        if (isGeneric(res)) return 3;
        if (isProduction(res)) return 4;
        return 5;
    };

    return _.sortBy(entries, ([res, num]) => [
        sortIndex(res),
        res.name,
        res.id,
    ]);
}

function isGeneric(entity: ResourceEntity) {
    return entity.id.startsWith("mge-") || entity.id.startsWith("pge-");
}

function isProduction(e: ResourceEntity) {
    return e.id.startsWith("pro-") || e.id.startsWith("pge-");
}

type PerformVyrobaProps = {
    vyroba: VyrobaTeamEntity;
    resources: Record<string, ResourceTeamEntity>;
    team: Team;
    onReset: () => void;
};
function PerformVyroba(props: PerformVyrobaProps) {
    const { data: entities, error: eError } = useEntities<ResourceEntity>();
    const { data: tiles, error: tError } = useSWR<any[]>("/game/map", fetcher);

    const [count, setCount] = useState(1);
    const [tile, setTile] = useState<string>();
    const [plunder, setPlunder] = useState(false);

    const vyroba = props.vyroba;

    useEffect(() => {
        if (!tiles || tile || !vyroba || !vyroba?.allowedTiles) return;
        const homeTile = tiles.find((t) => t?.homeTeam === props.team.id);
        setTile(homeTile.entity);
    }, [tiles, props.team, vyroba]);

    if (!entities || !tiles) {
        return (
            <LoadingOrError
                error={eError || tError}
                message="Nepodařilo se načíst entity"
            />
        );
    }

    const handleCountChange = (x: number) => {
        setCount(x >= 0 ? x : 0);
    };

    let sortedTiles = tiles.sort((a, b) => a.name.localeCompare(b.name));

    return (
        <PerformAction
            actionName={`Výroba ${count}× ${vyroba.name} pro tým ${props.team.name}`}
            actionId="VyrobaAction"
            actionArgs={{
                team: props.team.id,
                tile,
                vyroba: props.vyroba.id,
                count,
                plunder,
            }}
            argsValid={(a) => Boolean(a.tile)}
            onFinish={() => props.onReset()}
            onBack={() => props.onReset()}
            extraPreview={
                <>
                    <FormRow label="Zadejte počet výrob:">
                        <SpinboxInput
                            value={count}
                            onChange={handleCountChange}
                        />
                    </FormRow>
                    <FormRow label="Vyberte pole mapy pro výrobu:">
                        <select
                            className="select field"
                            value={tile ?? ""}
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
                                        {t.homeTeam
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
                        {count}× {vyroba.name} →{" "}
                        {count * Number(vyroba.reward[1])}×{" "}
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
        return <LoadingOrError error={error} message="Něco se pokazilo" />;

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
                                <EntityTag id={r} /> (max {maxV}):
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
                label={!isEmpty ? "Vybrat" : "Tým nemá nic ve skladu"}
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
