import { produce } from "immer";
import { useAtom, useSetAtom } from "jotai";
import { RESET } from "jotai/utils";
import _ from "lodash";
import { ChangeEvent, useEffect, useState } from "react";
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
    useTeamSpecialResources,
    useTeamStorage,
    useTeamVyrobas,
} from "../elements/entities";
import { useMapTileStates } from "../elements/states";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    Decimal,
    ResourceEntity,
    ResourceId,
    ResourceTeamEntity,
    Team,
    VyrobaTeamEntity,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
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
            <FormRow label="Vyber výrobu:">
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
    const { tiles, error: tError } = useMapTileStates();

    const [count, setCount] = useState(1);
    const [tile, setTile] = useState<string>();

    const vyroba = props.vyroba;

    useEffect(() => {
        if (!tiles || tile || !vyroba || !vyroba?.allowedTiles) return;
        const homeTile = tiles.find((t) => t?.homeTeam === props.team.id);
        console.assert(!_.isNil(homeTile), "No home tile");
        setTile(homeTile?.entity);
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
    const { storage, error, mutate } = useTeamStorage(props.team);
    const [toWithdraw, setToWithdraw] = useState<Record<ResourceId, number>>(
        {}
    );
    const { data: specialres } = useTeamSpecialResources(props.team.id);
    const setVyrobaAction = useSetAtom(urlVyrobaActionAtom);

    if (!storage) {
        return <LoadingOrError error={error} message="Něco se pokazilo" />;
    }

    const isEmpty = Object.keys(storage).length === 0;

    const toWithdrawSum = _.sum(Object.values(toWithdraw));
    const sumClassName =
        !_.isNil(specialres) &&
        toWithdrawSum > Number(specialres.withdraw_capacity)
            ? "text-red-500"
            : undefined;

    return (
        <>
            <h2>
                Zadejte kolik vybrat ze skladu (
                <span className={sumClassName}>{toWithdrawSum}</span>/
                {specialres?.withdraw_capacity ?? "??"})
            </h2>

            {Object.entries(storage).map(([resId, decMaxValue]) => {
                const maxValue = _.floor(Number(decMaxValue));
                return (
                    <FormRow
                        key={resId}
                        label={
                            <>
                                <span
                                    className="cursor-pointer"
                                    onClick={() => {
                                        setToWithdraw(
                                            produce(toWithdraw, (next) => {
                                                next[resId] = maxValue;
                                            })
                                        );
                                    }}
                                >
                                    <EntityTag id={resId} /> (max {maxValue}
                                    ):
                                </span>
                            </>
                        }
                    >
                        <SpinboxInput
                            value={_.get(toWithdraw, resId, 0)}
                            onChange={(v) => {
                                setToWithdraw(
                                    produce(toWithdraw, (next) => {
                                        next[resId] = _.clamp(v, 0, maxValue);
                                    })
                                );
                            }}
                        />
                    </FormRow>
                );
            })}

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
