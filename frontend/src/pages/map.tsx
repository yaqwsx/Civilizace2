import classNames from "classnames";
import produce from "immer";
import { useAtom, useSetAtom } from "jotai";
import { RESET, atomWithHash } from "jotai/utils";
import _ from "lodash";
import { useState } from "react";
import useSWR from "swr";
import {
    Button,
    Dialog,
    FormRow,
    LoadingOrError,
    SpinboxInput,
} from "../elements";
import { PerformAction, PerformNoInitAction } from "../elements/action";
import { ArmyGoalSelect } from "../elements/army";
import { EntityTag, useEntities } from "../elements/entities";
import {
    BuildingTeamSelect,
    BuildingUpgradeTeamSelect,
    TeamAttributeSelect,
    TileTeamSelect,
    VyrobaTeamSelect,
} from "../elements/entities_select";
import { ErrorMessage } from "../elements/messages";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    ArmyGoal,
    ArmyMode,
    BuildingEntity,
    BuildingUpgradeTeamEntity,
    Decimal,
    MapTileTeamEntity,
    ResourceEntity,
    ResourceId,
    Team,
    TeamArmy,
    TeamAttributeTeamEntity,
    VyrobaId,
    VyrobaTeamEntity,
} from "../types";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";

export function MapMenu() {
    return null;
}

enum MapActionType {
    feeding,
    automateFeeding,
    army,
    building,
    buildingUpgrade,
    addAttribute,
    revertVyroba,
    trade,
    addCulture,
}

const urlMapActionAtom = atomWithHash<MapActionType | null>("mapAction", null);

function MapActionColorClassNames(action: MapActionType): string {
    switch (action) {
        case MapActionType.feeding:
        case MapActionType.automateFeeding:
            return "bg-green-600 hover:bg-green-700";
        case MapActionType.army:
            return "bg-orange-600 hover:bg-orange-700";
        case MapActionType.building:
        case MapActionType.buildingUpgrade:
        case MapActionType.addAttribute:
            return "bg-purple-600 hover:bg-purple-700";
        case MapActionType.revertVyroba:
            return "bg-red-500 hover:bg-red-600";
        case MapActionType.trade:
            return "bg-yellow-500 hover:bg-yellow-600";
        case MapActionType.addCulture:
            return "bg-blue-500 hover:bg-blue-600";
        default:
            const exhaustiveCheck: never = action;
            return "bg-gray-500 hover:bg-gray-600"; // For invalid Enum value
    }
}

function MapActionName(action: MapActionType): string {
    switch (action) {
        case MapActionType.feeding:
            return "Krmení";
        case MapActionType.automateFeeding:
            return "Automatizovat krmení";
        case MapActionType.army:
            return "Armáda";
        case MapActionType.building:
            return "Stavět budovu";
        case MapActionType.buildingUpgrade:
            return "Vylepšit budovu";
        case MapActionType.addAttribute:
            return "Získat vlastnost";
        case MapActionType.revertVyroba:
            return "Vrátit výrobu";
        case MapActionType.trade:
            return "Obchodovat";
        case MapActionType.addCulture:
            return "Přidat kulturu";
        default:
            const exhaustiveCheck: never = action;
            return String(action); // For invalid Enum value
    }
}

function MapActionAgenda(props: {
    action: MapActionType;
    team: Team;
}): JSX.Element {
    switch (props.action) {
        case MapActionType.feeding:
            return <FeedingAgenda team={props.team} />;
        case MapActionType.automateFeeding:
            return <AutomateFeedingAgenda team={props.team} />;
        case MapActionType.army:
            return <ArmyManipulation team={props.team} />;
        case MapActionType.building:
            return <BuildingAgenda team={props.team} />;
        case MapActionType.buildingUpgrade:
            return <BuildingUpgradeAgenda team={props.team} />;
        case MapActionType.addAttribute:
            return <AddAttributeAgenda team={props.team} />;
        case MapActionType.revertVyroba:
            return <RevertVyrobaAgenda team={props.team} />;
        case MapActionType.trade:
            return <TradeAgenda team={props.team} />;
        case MapActionType.addCulture:
            return <CultureAgenda team={props.team} />;
        default:
            const exhaustiveCheck: never = props.action;
            return <></>; // For invalid Enum value
    }
}

export function MapAgenda() {
    useHideMenu();
    const { team, setTeam, error, success } = useTeamFromUrl();
    const [action, setAction] = useAtom(urlMapActionAtom);

    if (!success) {
        return <LoadingOrError error={error} message="Něco se nepovedlo." />;
    }

    const handleTeamChange = (t?: Team) => {
        setTeam(t);
        setAction(RESET);
    };

    return (
        <>
            <h1>Stanoviště s mapou</h1>
            <FormRow label="Vyber tým:">
                <TeamSelector onChange={handleTeamChange} activeId={team?.id} />
            </FormRow>
            {team ? (
                <>
                    <FormRow label="Vyberte akci:">
                        {Object.values(MapActionType)
                            .map(Number)
                            .filter((value) => !isNaN(value))
                            .map((value) => value as MapActionType)
                            .map((action) => {
                                const colorClassNames =
                                    MapActionColorClassNames(action);
                                return (
                                    <Button
                                        key={action}
                                        label={MapActionName(action)}
                                        className={`m-2 flex-1 ${colorClassNames}`}
                                        onClick={() => setAction(action)}
                                    />
                                );
                            })}
                    </FormRow>
                    <TeamRowIndicator team={team} />

                    {!_.isNil(action) ? (
                        <MapActionAgenda action={action} team={team} />
                    ) : null}
                </>
            ) : null}
        </>
    );
}

export function CultureAgenda(props: { team: Team }) {
    const [culture, setCulture] = useState(0);
    const setAction = useSetAtom(urlMapActionAtom);

    return (
        <PerformNoInitAction
            actionId="AddCultureAction"
            actionName={`Udělit kulturu týmu ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
                culture,
            }}
            onFinish={() => setAction(RESET)}
            onBack={() => {}}
            extraPreview={
                <>
                    <FormRow label="Kolik přidat kultury?">
                        <SpinboxInput value={culture} onChange={setCulture} />
                    </FormRow>
                </>
            }
        />
    );
}

export function BuildingAgenda(props: { team: Team }) {
    const setAction = useSetAtom(urlMapActionAtom);
    const [building, setBuilding] = useState<BuildingEntity>();
    const [tile, setTile] = useState<MapTileTeamEntity>();

    return (
        <>
            <h1>Stavění budovy pro tým {props.team.name}</h1>
            <PerformAction
                actionId="BuildAction"
                actionName={`Stavba budovy týmu ${props.team.name}`}
                actionArgs={{
                    team: props.team.id,
                    tile: tile?.id,
                    building: building?.id,
                }}
                argsValid={(a) => Boolean(a?.building && a?.tile)}
                onBack={() => {}}
                onFinish={() => {
                    setAction(RESET);
                }}
                extraPreview={
                    <>
                        <FormRow
                            label="Vyberte budovu"
                            error={!building ? "Je třeba vybrat budovu" : null}
                        >
                            <BuildingTeamSelect
                                team={props.team}
                                value={building}
                                onChange={setBuilding}
                            />
                        </FormRow>
                        <FormRow
                            label="Vyberte políčko"
                            error={!tile ? "Je třeba vybrat pole" : null}
                        >
                            <TileTeamSelect
                                team={props.team}
                                value={tile}
                                onChange={setTile}
                                sortBy={(tile) => (tile.is_home ? 0 : 1)}
                            />
                        </FormRow>
                    </>
                }
            />
        </>
    );
}

export function BuildingUpgradeAgenda(props: { team: Team }) {
    const { data: availableUpgrades, error } = useSWR<any>(
        `game/teams/${props.team.id}/building_upgrades`,
        fetcher
    );
    const setAction = useSetAtom(urlMapActionAtom);
    const [tile, setTile] = useState<MapTileTeamEntity>();
    const [upgrade, setUpgrade] = useState<BuildingUpgradeTeamEntity>();

    if (!availableUpgrades) {
        return <LoadingOrError error={error} message="Něco se pokazilo" />;
    }

    return (
        <>
            <h1>Stavění vylepšení budovy pro tým {props.team.name}</h1>
            <PerformAction
                actionId="BuildUpgradeAction"
                actionName={`Stavba vylepšení budovy pro tým ${props.team.name}`}
                actionArgs={{
                    team: props.team.id,
                    tile: tile?.id,
                    upgrade: upgrade?.id,
                }}
                argsValid={(a: any) => (a?.upgrade && a?.tile) || false}
                onBack={() => {}}
                onFinish={() => {
                    setAction(RESET);
                }}
                extraPreview={
                    <>
                        <FormRow
                            label="Vyberte políčko"
                            error={!tile ? "Je třeba vybrat pole" : null}
                        >
                            <TileTeamSelect
                                team={props.team}
                                value={tile}
                                onChange={setTile}
                                sortBy={(tile) => (tile.is_home ? 0 : 1)}
                            />
                        </FormRow>
                        <FormRow
                            label="Vyberte vylepšení"
                            error={
                                !upgrade ? "Je třeba vybrat vylepšení" : null
                            }
                        >
                            <BuildingUpgradeTeamSelect
                                team={props.team}
                                value={upgrade}
                                onChange={setUpgrade}
                            />
                        </FormRow>
                    </>
                }
            />
        </>
    );
}

export function AddAttributeAgenda(props: { team: Team }) {
    const setAction = useSetAtom(urlMapActionAtom);
    const [attribute, setAttribute] = useState<TeamAttributeTeamEntity>();

    return (
        <PerformAction
            actionId="AcquireTeamAttributeAction"
            actionName={`Získat vlastnost pro tým ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
                attribute: attribute?.id,
            }}
            argsValid={(a) => Boolean(a?.team && a?.attribute)}
            onBack={() => {}}
            onFinish={() => {
                setAction(RESET);
            }}
            extraPreview={
                <>
                    <h1>Získat vlastnost pro tým {props.team.name}</h1>
                    <FormRow
                        label="Vyberte vlastnost"
                        error={!attribute ? "Je třeba vybrat vlastnost" : null}
                    >
                        <TeamAttributeSelect
                            value={attribute}
                            onChange={setAttribute}
                            filter={(value) => !value.owned}
                        />
                    </FormRow>
                </>
            }
        />
    );
}

export function RevertVyrobaAgenda(props: { team: Team }) {
    const setAction = useSetAtom(urlMapActionAtom);
    const { data: employees, error } = useSWR<Record<VyrobaId, number>>(
        `game/teams/${props.team.id}/employees`,
        fetcher
    );
    const [vyroba, setVyroba] = useState<VyrobaTeamEntity>();
    const [count, setCount] = useState<number>(1);

    if (!employees) {
        return <LoadingOrError error={error} message="Něco se pokazilo" />;
    }

    if (Object.keys(employees).length === 0) {
        return (
            <ErrorMessage>
                Tým nemá žádné výroby, které by mohl vrátit
            </ErrorMessage>
        );
    }

    return (
        <PerformAction
            actionName={`Vrácení výroby${
                vyroba ? ` ${count}× ${vyroba.name}` : ""
            } pro tým ${props.team.name}`}
            actionId="VyrobaRevertAction"
            actionArgs={{
                team: props.team.id,
                vyroba: vyroba?.id,
                count,
            }}
            argsValid={(a) => !_.isNil(a.vyroba)}
            onFinish={() => setAction(RESET)}
            onBack={() => setAction(RESET)}
            extraPreview={
                <>
                    <FormRow label="Vyber výrobu na vrácení:">
                        <VyrobaTeamSelect
                            value={vyroba}
                            team={props.team}
                            onChange={setVyroba}
                            filter={(value) => (employees[value.id] ?? 0) > 0}
                        />
                    </FormRow>
                    <FormRow
                        label={`Zadejte počet výrob k vrácení${
                            !_.isNil(vyroba)
                                ? ` (max ${employees[vyroba.id] ?? 0})`
                                : ""
                        }:`}
                    >
                        <SpinboxInput
                            value={count}
                            onChange={(v) => setCount(v >= 0 ? v : 0)}
                        />
                    </FormRow>
                </>
            }
        />
    );
}

export function TradeAgenda(props: { team: Team }) {
    const setAction = useSetAtom(urlMapActionAtom);
    const [recipient, setRecipient] = useState<Team>();
    const [resources, setResources] = useState<Record<ResourceId, number>>({});

    const { data: productions, error } = useSWR<Record<ResourceId, Decimal>>(
        `game/teams/${props.team.id}/productions`,
        fetcher
    );

    if (!productions) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    }

    const updateResources = (prodId: string, amount: number) => {
        const available = Number(productions[prodId]);
        if (amount < 0) {
            amount = 0;
        } else if (amount > available) {
            amount = available;
        }
        setResources(
            produce(resources, (orig) => {
                orig[prodId] = amount;
            })
        );
    };

    if (Object.keys(productions).length === 0) {
        return (
            <ErrorMessage>
                Tým nemá žádné produkce, které by mohl obchodovat
            </ErrorMessage>
        );
    }

    return (
        <PerformAction
            actionId="TradeAction"
            actionName={`Obchod ${props.team.name} → ${recipient?.name ?? ""}`}
            actionArgs={{
                team: props.team.id,
                receiver: recipient?.id,
                resources,
            }}
            argsValid={(a: any) =>
                Object.keys(a.resources).length > 0 && !_.isNil(a.receiver)
            }
            onBack={() => {}}
            onFinish={() => {
                setAction(RESET);
            }}
            extraPreview={
                <>
                    <h1>Obchodovat</h1>
                    <FormRow label="Příjemce:">
                        <TeamSelector
                            allowNull={false}
                            activeId={recipient?.id}
                            onChange={setRecipient}
                            ignoredTeam={props.team}
                        />
                    </FormRow>
                    {Object.entries(productions).map(([prodId, max]) => {
                        return (
                            <FormRow
                                key={prodId}
                                label={
                                    <>
                                        <EntityTag id={prodId} /> (max {max})
                                    </>
                                }
                            >
                                <SpinboxInput
                                    value={resources[prodId] ?? 0}
                                    onChange={(v) => updateResources(prodId, v)}
                                />
                            </FormRow>
                        );
                    })}
                </>
            }
        />
    );
}

export function ArmyManipulation(props: { team: Team; onFinish?: () => void }) {
    const {
        data: armies,
        error: armyError,
        mutate,
    } = useSWR<Record<number, TeamArmy>>(
        `game/teams/${props.team.id}/armies`,
        fetcher
    );

    if (!armies) {
        return (
            <LoadingOrError error={armyError} message={"Něco se pokazilo"} />
        );
    }
    return (
        <>
            <h1>Manipulace s armádami týmu {props.team.name}</h1>
            <div className="w-full flex-wrap md:flex">
                {Object.entries(armies).map(([k, a]) => (
                    <ArmyBadge
                        key={a.index}
                        team={props.team}
                        army={a}
                        mutate={mutate}
                    />
                ))}
            </div>
        </>
    );
}

export function ArmyDescription(props: { army: TeamArmy }) {
    const modeString = function (mode: ArmyMode) {
        switch (mode) {
            case ArmyMode.Idle:
                return "čeká na rozkazy";
            case ArmyMode.Marching:
                return "přesun";
            case ArmyMode.Occupying:
                return "okupace";
            default:
                const exhaustiveCheck: never = mode;
                return String(mode); // For invalid Enum value
        }
    };

    let attributes: [string, JSX.Element][] = [
        ["Úroveň", <>{props.army.level}</>],
        [
            "Stojí na",
            props.army.tile ? (
                <EntityTag id={props.army.tile} />
            ) : (
                <>domovském políčku</>
            ),
        ],
        ["Stav", <>{modeString(props.army.mode)}</>],
    ];
    if (props.army.mode !== "Idle") {
        attributes.push(["Vybavení", <>{props.army.equipment}</>]);
    }

    return (
        <table className="w-full table-fixed">
            <tbody>
                {attributes.map(([k, v]) => (
                    <tr key={k}>
                        <td className="pr-3 text-right font-bold">{k}: </td>
                        <td className="text-left">{v}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export function ArmyName(props: { army: TeamArmy }) {
    return (
        <>
            {props.army.name} {"✱".repeat(props.army.level)}
        </>
    );
}

function ArmyBadge(props: { team: Team; army: TeamArmy; mutate: () => void }) {
    const [selectedAction, setSelectedAction] = useState("");

    let className = classNames(
        "bg-white rounded p-4 mx-4 my-4 cursor-pointer shadow-lg flex flex-wrap md:flex-1"
    );

    let ActionForm = {
        armyDeploy: ArmyDeployForm,
        armyRetreat: ArmyRetreatForm,
        armyUpgrade: ArmyUpgradeForm,
    }[selectedAction];

    return (
        <div className={className}>
            <h3 className="w-full">
                Armáda <ArmyName army={props.army} />
            </h3>
            <div className="w-full md:w-2/3">
                <ArmyDescription army={props.army} />
            </div>
            <div className="w-full px-3 md:w-1/3">
                <Button
                    label="Vyslat armádu"
                    disabled={props.army.mode != "Idle"}
                    className="my-2 w-full bg-orange-600 hover:bg-orange-700"
                    onClick={() => setSelectedAction("armyDeploy")}
                />
                <Button
                    label="Stáhnout armádu"
                    disabled={props.army.mode != "Occupying"}
                    className="my-2 w-full bg-green-600 hover:bg-green-700"
                    onClick={() => setSelectedAction("armyRetreat")}
                />
                <Button
                    label="Upgradovat armádu"
                    disabled={
                        props.army.mode != "Idle" || props.army.level == 3
                    }
                    className="my-2 w-full bg-blue-600 hover:bg-blue-700"
                    onClick={() => setSelectedAction("armyUpgrade")}
                />
            </div>
            {ActionForm ? (
                <ActionForm
                    team={props.team}
                    army={props.army}
                    onFinish={() => {
                        setSelectedAction("");
                        props.mutate();
                    }}
                />
            ) : null}
        </div>
    );
}

function ArmyDeployForm(props: {
    team: Team;
    army: TeamArmy;
    onFinish: () => void;
}) {
    const [tile, setTile] = useState<MapTileTeamEntity>();
    const [goal, setGoal] = useState<ArmyGoal>(ArmyGoal.Occupy);
    const [equipment, setEquipment] = useState(1);
    const [friendlyTeam, setFriendlyTeam] = useState<Team>();

    return (
        <Dialog onClose={props.onFinish}>
            <PerformAction
                actionName={`Vyslat armádu ${props.army.name} týmu ${props.team.name}`}
                actionId="ArmyDeployAction"
                actionArgs={{
                    team: props.team.id,
                    armyIndex: props.army.index,
                    tile: tile?.id,
                    goal,
                    equipment,
                    friendlyTeam: friendlyTeam?.id,
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
                argsValid={(a) => Boolean(a.tile && a.equipment >= 0)}
                extraPreview={
                    <>
                        <h1>Zadejte extra parametry</h1>
                        <FormRow
                            label="Cílová destinace"
                            error={!tile ? "Je třeba vyplnit" : null}
                        >
                            <TileTeamSelect
                                team={props.team}
                                value={tile}
                                onChange={setTile}
                            />
                        </FormRow>
                        <FormRow label="Mód vyslání">
                            <ArmyGoalSelect value={goal} onChange={setGoal} />
                        </FormRow>
                        <FormRow label="Vyberte výbavu:">
                            <SpinboxInput
                                value={equipment}
                                onChange={(v) => {
                                    if (v >= 0) {
                                        setEquipment(v);
                                    }
                                }}
                            />
                        </FormRow>
                        <FormRow label="Spřátelený tým:">
                            <TeamSelector
                                allowNull
                                activeId={friendlyTeam?.id}
                                onChange={setFriendlyTeam}
                            />
                        </FormRow>
                    </>
                }
            />
        </Dialog>
    );
}

function ArmyRetreatForm(props: {
    team: Team;
    army: TeamArmy;
    onFinish: () => void;
}) {
    return (
        <Dialog onClose={props.onFinish}>
            <PerformAction
                actionName={
                    <>
                        Stáhnout armádu <ArmyName army={props.army} /> týmu{" "}
                        {props.team.name}
                    </>
                }
                actionId="ArmyRetreatAction"
                actionArgs={{
                    team: props.team.id,
                    armyIndex: props?.army?.index,
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
            />
        </Dialog>
    );
}

function ArmyUpgradeForm(props: {
    team: Team;
    army: TeamArmy;
    onFinish: () => void;
}) {
    return (
        <Dialog onClose={props.onFinish}>
            <PerformAction
                actionName={
                    <>
                        Vylepšit armádu <ArmyName army={props.army} /> týmu{" "}
                        {props.team.name}
                    </>
                }
                actionId="ArmyUpgradeAction"
                actionArgs={{
                    team: props.team.id,
                    armyIndex: props.army.index,
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
            />
        </Dialog>
    );
}

function FeedingForm(props: {
    team: Team;
    feeding: Record<string, number>;
    updateResource: (resId: string, value: number) => void;
}) {
    const { data: feedReq, error: fError } = useSWR<any>(
        `/game/teams/${props.team.id}/feeding`,
        fetcher
    );
    const { data: entities, error: eError } = useEntities<ResourceEntity>();
    if (!feedReq || !entities) {
        return (
            <LoadingOrError
                error={fError || eError}
                message="Něco se nepovedlo"
            />
        );
    }

    let automatedResIds = feedReq.automated.map((x: any) => x[0]);
    // @ts-ignore
    let automatedRes = feedReq.automated.map(([rId, recommended]) => [
        entities[rId],
        recommended,
    ]);
    let remaingRes = Object.values(entities)
        .filter(
            (e: any) =>
                e.id.startsWith("mat-") && !automatedResIds.includes(e.id)
        )
        .sort((a, b) => a.name.localeCompare(b.name));

    let missing =
        Object.values(props.feeding).reduce((a, b) => a + b, 0) -
        feedReq.tokensRequired;

    return (
        <>
            <h1>Krmení týmu {props.team.name}</h1>
            <FormRow label="Parametry krmení">
                <span className="mx-3">Kast: {feedReq.casteCount}, </span>
                <span className="mx-3">
                    Vyžadováno žetonů: {feedReq.tokensRequired}{" "}
                    {missing < 0 && (
                        <span className="font-bold text-red-500">
                            (chybí {-missing})
                        </span>
                    )}
                    ,{" "}
                </span>
                <span className="mx-3">
                    Žetonů na kastu: {feedReq.tokensPerCaste}
                </span>
            </FormRow>
            <div>
                {automatedRes.map(([r, recommended]: any) => (
                    <FormRow
                        key={r.id}
                        label={
                            <>
                                <EntityTag id={r.id} />
                                <br />
                                <span className="text-sm">
                                    (doporučeno {recommended}
                                </span>
                                )
                            </>
                        }
                    >
                        <SpinboxInput
                            value={_.get(props.feeding, r.id, 0)}
                            onChange={(v) => props.updateResource(r.id, v)}
                        />
                    </FormRow>
                ))}
                {remaingRes.map((r) => (
                    <FormRow
                        key={r.id}
                        label={
                            <>
                                <EntityTag id={r.id} />
                            </>
                        }
                    >
                        <SpinboxInput
                            value={_.get(props.feeding, r.id, 0)}
                            onChange={(v) => props.updateResource(r.id, v)}
                        />
                    </FormRow>
                ))}
            </div>

            {missing < 0 && (
                <ErrorMessage>
                    Nemáš dost žetonů, aby nikdo neumřel (chybí {-missing}).
                    Opravdu takovou akci chceš zadat?
                    <div style={{ fontSize: "8px" }}>
                        (a Maara si myslí, že je tě třeba ještě varovat extra a
                        oranžový rámeček dole nestačí)
                    </div>
                </ErrorMessage>
            )}
        </>
    );
}

export function FeedingAgenda(props: { team: Team }) {
    const [feeding, setFeeding] = useState<Record<string, number>>({});
    const setAction = useSetAtom(urlMapActionAtom);

    let updateResource = (rId: string, v: number) => {
        if (v < 0) v = 0;
        setFeeding(
            produce(feeding, (orig) => {
                orig[rId] = v;
            })
        );
    };

    return (
        <PerformAction
            actionId="FeedAction"
            actionName={`Krmení týmu ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
                materials: feeding,
            }}
            extraPreview={
                <FeedingForm
                    team={props.team}
                    feeding={feeding}
                    updateResource={updateResource}
                />
            }
            onBack={() => {}}
            onFinish={() => {
                setAction(RESET);
            }}
        />
    );
}

export function AutomateFeedingAgenda(props: { team: Team }) {
    const [productions, setProductions] = useState<Record<string, number>>({});
    const {
        data: availableProductions,
        error,
        mutate,
    } = useSWR<any>(`game/teams/${props.team.id}/resources`, fetcher);
    const setAction = useSetAtom(urlMapActionAtom);

    if (!availableProductions) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    }

    let food = Object.values(availableProductions);

    let updateResource = (rId: string, v: number) => {
        if (v < 0) v = 0;
        if (v > availableProductions[rId].available)
            v = availableProductions[rId].available;
        setProductions(
            produce(productions, (orig) => {
                orig[rId] = v;
            })
        );
    };

    return (
        <PerformAction
            actionId="GranaryAction"
            actionName={`Automatizace krmení ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
                productions: productions,
            }}
            argsValid={(a: any) => Object.keys(a.productions).length > 0}
            extraPreview={
                <>
                    {Object.keys(food).length > 0
                        ? food.map((a: any) => (
                              <FormRow
                                  key={a.id}
                                  label={
                                      <>
                                          <EntityTag id={a.id} /> (max{" "}
                                          {availableProductions[a.id].available}
                                          )
                                      </>
                                  }
                              >
                                  <SpinboxInput
                                      value={_.get(productions, a.id, 0)}
                                      onChange={(v) => updateResource(a.id, v)}
                                  />
                              </FormRow>
                          ))
                        : "Tým nemá žádné produkce jídla či luxusu. Není možné automatizovat."}
                </>
            }
            onBack={() => {}}
            onFinish={() => {
                setAction(RESET);
            }}
        />
    );
}
