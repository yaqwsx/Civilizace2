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
import { EntityTag } from "../elements/entities";
import { TileTeamSelect } from "../elements/entities_select";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    useTeamResources,
    useTeamSpecialResources,
    useTeamStorage,
    useTeamTiles,
    useTeamVyrobas,
} from "../elements/team_view";
import {
    Decimal,
    MapTileTeamEntity,
    ResourceEntity,
    ResourceId,
    ResourceTeamEntity,
    Team,
    VyrobaTeamEntity,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { useHideMenu } from "./atoms";

export const urlEntityAtom = stringAtomWithHash("entity");
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
    const { data: vyrobas, error: vError } = useTeamVyrobas(props.team);
    const [vyrobaId, setVyrobaId] = useAtom(urlEntityAtom);

    if (!vyrobas) {
        return (
            <LoadingOrError
                error={vError}
                message="Nemohu načíst výroby týmu."
            />
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

function useTeamHomeTile(team: Team): {
    homeTile?: MapTileTeamEntity;
    error: any;
} {
    const { data: tiles, error } = useTeamTiles(team);

    if (_.isNil(tiles) || error) {
        return { error };
    }

    const homeTile = Object.values(tiles).find((t) => t.is_home);
    if (_.isNil(homeTile)) {
        console.error("No home tile of team", team, tiles);
        return { error: `No home tile of team ${team.name}` };
    }

    return { homeTile, error };
}

type PerformVyrobaProps = {
    vyroba: VyrobaTeamEntity;
    team: Team;
    onReset: () => void;
};
function PerformVyroba(props: PerformVyrobaProps) {
    const [count, setCount] = useState(1);
    const [tile, setTile] = useState<MapTileTeamEntity>();

    const { homeTile } = useTeamHomeTile(props.team);

    useEffect(() => {
        if (!homeTile || !props.vyroba || !props.vyroba?.allowedTiles) {
            return;
        }
        setTile(homeTile);
    }, [props.team, homeTile, props.vyroba]);

    return (
        <PerformAction
            actionName={`Výroba ${count}× ${props.vyroba.name} pro tým ${props.team.name}`}
            actionId="VyrobaAction"
            actionArgs={{
                team: props.team.id,
                tile: tile?.id,
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
                            onChange={(v) => setCount(Math.max(v, 1))}
                        />
                    </FormRow>
                    <FormRow label="Vyberte pole mapy pro výrobu:">
                        <TileTeamSelect
                            team={props.team}
                            value={tile}
                            onChange={setTile}
                            sortBy={"-is_home"}
                        />
                    </FormRow>
                    <h2>
                        {count}× {props.vyroba.name} →{" "}
                        {count * Number(props.vyroba.reward[1])}×{" "}
                        <EntityTag id={props.vyroba.reward[0]} />
                    </h2>
                </>
            }
        />
    );
}

function WithdrawStorage(props: { team: Team }) {
    const [submitting, setSubmitting] = useState(false);
    const { data: storage, error, mutate } = useTeamStorage(props.team);
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
