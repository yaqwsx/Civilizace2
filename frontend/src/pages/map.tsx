import classNames from "classnames";
import produce from "immer";
import { useAtom, useSetAtom } from "jotai";
import { RESET, atomWithHash } from "jotai/utils";
import _ from "lodash";
import { useEffect, useState } from "react";
import {
    Button,
    Dialog,
    FormRow,
    LoadingOrError,
    SpinboxInput,
} from "../elements";
import { PerformAction, PerformNoInitAction } from "../elements/action";
import { ArmyGoalSelect } from "../elements/army";
import { EntityTag } from "../elements/entities";
import {
    BuildingTeamSelect,
    BuildingUpgradeTeamSelect,
    TeamAttributeSelect,
    TileTeamSelect,
    VyrobaTeamSelect,
} from "../elements/entities_select";
import { ErrorMessage } from "../elements/messages";
import { urlReaderEntityAtom } from "../elements/scanner";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    useTeamArmies,
    useTeamBuildingUpgrades,
    useTeamBuildings,
    useTeamEmployees,
    useTeamProductions,
    useTeamTeamAttributes,
    useTeamVyrobas,
} from "../elements/team_view";
import {
    ArmyGoal,
    ArmyMode,
    BuildingTeamEntity,
    BuildingUpgradeTeamEntity,
    MapTileTeamEntity,
    ResourceId,
    Team,
    TeamArmy,
    TeamAttributeTeamEntity,
    VyrobaTeamEntity,
} from "../types";
import { useHideMenu } from "./atoms";

export function MapMenu() {
    return null;
}

export enum MapActionType {
    feeding,
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
    const [building, setBuilding] = useState<BuildingTeamEntity>();
    const [tile, setTile] = useState<MapTileTeamEntity>();

    const [entity, setEntity] = useAtom(urlReaderEntityAtom);
    const { data: buildings } = useTeamBuildings(props.team);
    useEffect(() => {
        if (buildings && entity) {
            setBuilding(buildings[entity]);
            setEntity(RESET);
        }
    }, [entity, buildings]);

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
    const setAction = useSetAtom(urlMapActionAtom);
    const [upgrade, setUpgrade] = useState<BuildingUpgradeTeamEntity>();
    const [tile, setTile] = useState<MapTileTeamEntity>();

    const [entity, setEntity] = useAtom(urlReaderEntityAtom);
    const { data: upgrades } = useTeamBuildingUpgrades(props.team);
    useEffect(() => {
        if (upgrades && entity) {
            setUpgrade(upgrades[entity]);
            setEntity(RESET);
        }
    }, [entity, upgrades]);

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
                argsValid={(a) => Boolean(a?.upgrade && a?.tile)}
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

    const [entity, setEntity] = useAtom(urlReaderEntityAtom);
    const { data: attributes } = useTeamTeamAttributes(props.team);
    useEffect(() => {
        if (attributes && entity) {
            setAttribute(attributes[entity]);
            setEntity(RESET);
        }
    }, [entity, attributes]);

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
    const { data: employees, error } = useTeamEmployees(props.team);
    const [vyroba, setVyroba] = useState<VyrobaTeamEntity>();
    const [count, setCount] = useState<number>(1);

    const [entity, setEntity] = useAtom(urlReaderEntityAtom);
    const { data: vyrobas } = useTeamVyrobas(props.team);
    useEffect(() => {
        if (vyrobas && entity) {
            setVyroba(vyrobas[entity]);
            setEntity(RESET);
        }
    }, [entity, vyrobas]);

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

    const { data: productions, error } = useTeamProductions(props.team);

    if (!productions) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    }

    const updateResources = (prodId: string, amount: number) => {
        setResources(
            produce(resources, (orig) => {
                orig[prodId] = _.clamp(amount, 0, Number(productions[prodId]));
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
            argsValid={(a) =>
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
    } = useTeamArmies(props.team);

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

export function FeedingAgenda(props: { team: Team }) {
    const setAction = useSetAtom(urlMapActionAtom);

    return (
        <PerformAction
            actionId="FeedAction"
            actionName={`Krmení týmu ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
            }}
            onBack={() => {}}
            onFinish={() => {
                setAction(RESET);
            }}
        />
    );
}
