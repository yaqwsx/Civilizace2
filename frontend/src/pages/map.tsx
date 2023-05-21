import classNames from "classnames";
import produce from "immer";
import { useAtom } from "jotai";
import { atomWithHash } from "jotai/utils";
import _, { rest } from "lodash";
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
import { ArmyGoalSelect, ArmySelectBox } from "../elements/army";
import { EntityTag, useEntities } from "../elements/entities";
import { BuildingSelect, TeamTileSelect, TileSelect } from "../elements/map";
import { ErrorMessage } from "../elements/messages";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import { EntityResource, Team, TeamEntityResource } from "../types";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";

export function MapMenu() {
    return null;
}

enum MapActiontype {
    none,
    building,
    buildRoad,
    feeding,
    automateFeeding,
    army,
    trade,
    discoverTile,
    addCulture,
}

const urlMapActionAtom = atomWithHash<MapActiontype>(
    "mapAction",
    MapActiontype.none,
    {
        serialize: (x) => String(x),
        deserialize: (x) =>
            x ? (parseInt(x) as MapActiontype) : MapActiontype.none,
    }
);

export function MapAgenda() {
    useHideMenu();
    const { team, setTeam, loading, error } = useTeamFromUrl();
    const [action, setAction] = useAtom(urlMapActionAtom);

    if (loading || error) {
        return (
            <LoadingOrError
                loading={loading}
                error={error}
                message="Něco se nepovedlo."
            />
        );
    }

    const handleTeamChange = (t?: Team) => {
        setTeam(t);
        setAction(MapActiontype.none);
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
                        <Button
                            label="Krmit"
                            className="m-2 flex-1 bg-green-600 hover:bg-green-700"
                            onClick={() => setAction(MapActiontype.feeding)}
                        />
                        <Button
                            label="Automatizovat krmení"
                            className="m-2 flex-1 bg-green-600 hover:bg-green-700"
                            onClick={() =>
                                setAction(MapActiontype.automateFeeding)
                            }
                        />
                        <Button
                            label="Armáda"
                            className="m-2 flex-1 bg-orange-600 hover:bg-orange-700"
                            onClick={() => setAction(MapActiontype.army)}
                        />
                        <Button
                            label="Stavět"
                            className="m-2 flex-1"
                            onClick={() => setAction(MapActiontype.building)}
                        />
                        <Button
                            label="Postavit cestu"
                            className="m-2 flex-1"
                            onClick={() => setAction(MapActiontype.buildRoad)}
                        />
                        <Button
                            label="Obchodovat"
                            className="m-2 flex-1 bg-yellow-500 hover:bg-yellow-600"
                            onClick={() => setAction(MapActiontype.trade)}
                        />
                        <Button
                            label="Objevit dílek"
                            className="m-2 flex-1 bg-blue-500 hover:bg-blue-600"
                            onClick={() =>
                                setAction(MapActiontype.discoverTile)
                            }
                        />
                        <Button
                            label="Přidat kulturu"
                            className="m-2 flex-1 bg-blue-500 hover:bg-blue-600"
                            onClick={() =>
                                setAction(MapActiontype.addCulture)
                            }
                        />
                    </FormRow>
                    <TeamRowIndicator team={team} />

                    {action == MapActiontype.army ? (
                        <ArmyManipulation team={team} />
                    ) : null}
                    {action == MapActiontype.building ? (
                        <BuildingAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.buildRoad ? (
                        <BuildRoadAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.feeding ? (
                        <FeedingAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.automateFeeding ? (
                        <AutomateFeedingAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.trade ? (
                        <TradeAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.discoverTile ? (
                        <DiscoverAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.addCulture ? (
                        <CultureAgenda team={team} />
                    ) : null}
                </>
            ) : null}
        </>
    );
}

export function DiscoverAgenda(props: { team: Team }) {
    const [tile, setTile] = useState<any>(undefined);
    const [action, setAction] = useAtom(urlMapActionAtom);

    return (
        <PerformAction
            actionId="DiscoverTileAction"
            actionName={`Objevit dílek mapy týmem ${props.team.name}`}
            argsValid={(a: any) => a?.team && a?.tile}
            actionArgs={{
                team: props.team.id,
                tile: tile?.id,
            }}
            onFinish={() => setAction(MapActiontype.none)}
            onBack={() => {}}
            extraPreview={
                <>
                    <FormRow label="Vyberte dílek">
                        <TileSelect value={tile} onChange={setTile} />
                    </FormRow>
                </>
            }
        />
    );
}

export function CultureAgenda(props: { team: Team }) {
    const [culture, setCulture] = useState<number>(0);
    const [action, setAction] = useAtom(urlMapActionAtom);

    return (
        <PerformNoInitAction
            actionId="AddCultureAction"
            actionName={`Udělit kulturu týmu ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
                culture: culture
            }}
            onFinish={() => setAction(MapActiontype.none)}
            onBack={() => {}}
            extraPreview={
                <>
                    <FormRow label="Kolik přidat kultury?">
                        <SpinboxInput value={culture} onChange={setCulture}/>
                    </FormRow>
                </>
            }
        />
    );
}

export function BuildingAgenda(props: { team: Team }) {
    const { data: availableBuildings, error } = useSWR<any>(
        `game/teams/${props.team.id}/buildings`,
        fetcher
    );
    const [action, setAction] = useAtom(urlMapActionAtom);
    const [building, setBuilding] = useState<any>(undefined);
    const [tile, setTile] = useState<any>(undefined);

    if (!availableBuildings || error) {
        return (
            <LoadingOrError
                loading={!availableBuildings && !error}
                error={error}
                message="Něco se pokazilo"
            />
        );
    }

    return (
        <>
            <h1>Stavění budovy pro tým {props.team.name}</h1>
            <PerformAction
                actionId="BuildAction"
                actionName={`Stavba budovy týmu ${props.team.name}`}
                actionArgs={{
                    team: props.team.id,
                    tile: tile?.entity.id,
                    building: building?.id,
                }}
                argsValid={(a: any) => (a?.building && a?.tile) || false}
                onBack={() => {}}
                onFinish={() => {
                    setAction(MapActiontype.none);
                }}
                extraPreview={
                    <>
                        <FormRow
                            label="Vyberte budovu"
                            error={!building ? "Je třeba vybrat budovu" : null}
                        >
                            <BuildingSelect
                                value={building}
                                onChange={setBuilding}
                                allowed={availableBuildings}
                            />
                        </FormRow>
                        <FormRow
                            label="Vyberte políčko"
                            error={!tile ? "Je třeba vybrat pole" : null}
                        >
                            <TeamTileSelect
                                team={props.team}
                                value={tile}
                                onChange={setTile}
                            />
                        </FormRow>
                    </>
                }
            />
        </>
    );
}

export function BuildRoadAgenda(props: { team: Team }) {
    const [action, setAction] = useAtom(urlMapActionAtom);
    const [tile, setTile] = useState<any>(undefined);

    return (
        <PerformAction
            actionId="BuildRoadAction"
            actionName={`Postavit cestu týmem ${props.team.name}`}
            actionArgs={{
                team: props.team.id,
                tile: tile?.entity?.id,
            }}
            argsValid={(a: any) => a?.tile || false}
            onBack={() => {}}
            onFinish={() => {
                setAction(MapActiontype.none);
            }}
            extraPreview={
                <>
                    <h1>Postavit cestu týmem {props.team.name}</h1>
                    <FormRow
                        label="Vyberte políčko kam se bude stavět"
                        error={!tile ? "Je třeba vybrat pole" : null}
                    >
                        <TeamTileSelect
                            team={props.team}
                            value={tile}
                            onChange={setTile}
                        />
                    </FormRow>
                </>
            }
        />
    );
}

export function TradeAgenda(props: { team: Team }) {
    const [action, setAction] = useAtom(urlMapActionAtom);
    const [recipient, setRecipient] = useState<Team | undefined>(undefined);
    const [resources, setResources] = useState<Record<string, number>>({});

    const {
        data: availableProductions,
        error,
        mutate,
    } = useSWR<any>(`game/teams/${props.team.id}/resources`, fetcher);

    if (!availableProductions) {
        return (
            <LoadingOrError
                loading={!availableProductions && !error}
                error={error}
                message="Něco se nepovedlo"
            />
        );
    }

    let updateResource = (rId: string, v: number) => {
        if (v < 0) v = 0;
        if (v > availableProductions[rId].available)
            v = availableProductions[rId].available;
        setResources(
            produce(resources, (orig) => {
                orig[rId] = v;
            })
        );
    };

    return (
        <PerformAction
            actionId="TradeAction"
            actionName={`Obchod ${props.team.name} → ${recipient?.name}`}
            actionArgs={{
                team: props.team.id,
                receiver: recipient?.id,
                resources: resources,
            }}
            argsValid={(a: any) =>
                Object.keys(a.resources).length > 0 && a.receiver !== undefined
            }
            onBack={() => {}}
            onFinish={() => {
                setAction(MapActiontype.none);
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
                    {Object.keys(availableProductions).length > 0
                        ? Object.values(availableProductions).map((a: any) => {
                              if (["res-prace", "res-obyvatel"].includes(a.id))
                                  return null;
                              return (
                                  <FormRow
                                      key={a.id}
                                      label={
                                          <>
                                              <EntityTag id={a.id} /> (max{" "}
                                              {
                                                  availableProductions[a.id]
                                                      .available
                                              }
                                              )
                                          </>
                                      }
                                  >
                                      <SpinboxInput
                                          value={_.get(resources, a.id, 0)}
                                          onChange={(v) =>
                                              updateResource(a.id, v)
                                          }
                                      />
                                  </FormRow>
                              );
                          })
                        : "Tým nemá žádné produkce které by mohl obchodovat"}
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
    } = useSWR<Record<number, any>>(
        `game/teams/${props.team.id}/armies`,
        fetcher
    );

    if (!armies) {
        return (
            <LoadingOrError
                loading={!armies && !armyError}
                error={armyError}
                message={"Něco se pokazilo"}
            />
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

export function ArmyDescription(props: { army: any; orgView: boolean }) {
    let modeMapping = {
        Idle: "čeká na rozkazy",
        Marching: "přesun",
        Occupying: "okupace",
    };

    let attributes = {
        // Úroveň: props.army.level,
        "Stojí na": props.army.tile ? (
            <EntityTag id={props.army.tile} />
        ) : (
            "domovském políčku"
        ),
        // @ts-ignore
        Stav: modeMapping[props.army.mode],
    };
    if (props.army.mode !== "Idle") {
        // @ts-ignore
        attributes["Vybavení"] = props.army.equipment;
    }

    return (
        <table className="w-full table-fixed">
            <tbody>
                {Object.entries(attributes).map(([k, v]) => (
                    <tr key={k}>
                        <td className="pr-3 text-right font-bold">{k}: </td>
                        <td className="text-left">{v}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export function ArmyName(props: { army: any }) {
    return (
        <>
            {props.army.name} {"✱".repeat(props.army.level)}
        </>
    );
}

function ArmyBadge(props: { team: Team; army: any; mutate: () => void }) {
    const [selectedAction, setSelectedAction] = useState("");

    let className = classNames(
        "bg-white rounded p-4 mx-4 my-4 cursor-pointer shadow-lg flex flex-wrap md:flex-1"
    );

    let ActionForm: any = {
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
                <ArmyDescription army={props.army} orgView={true} />
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
                    disabled={props.army.mode != "Idle" || props.army.level == 3}
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
    army: any;
    onFinish: () => void;
}) {
    const [tile, setTile] = useState<any>(null);
    const [goal, setGoal] = useState<any>(0);
    const [equipment, setEquipment] = useState<number>(1);
    const [friendlyTeam, setFriendlyTeam] = useState<Team | undefined>(
        undefined
    );

    return (
        <Dialog onClose={props.onFinish}>
            <PerformAction
                actionName={`Vyslat armádu ${props.army.prestige} týmu ${props.team.name}`}
                actionId="ArmyDeployAction"
                actionArgs={{
                    team: props.team.id,
                    armyIndex: props.army.index,
                    tile: tile?.entity.id,
                    goal: goal,
                    equipment: equipment,
                    friendlyTeam: friendlyTeam?.id,
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
                argsValid={(a: any) => a.tile && a.equipment >= 0}
                extraPreview={
                    <>
                        <h1>Zadejte extra parametry</h1>
                        <FormRow
                            label="Cílová destinace"
                            error={!tile ? "Je třeba vyplnit" : null}
                        >
                            <TeamTileSelect
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
                                    if (v < 0) return;
                                    setEquipment(v);
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
    army: any;
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
    army: any;
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
    const { data: entities, error: eError } = useEntities<EntityResource>();
    if (!feedReq || !entities) {
        return (
            <LoadingOrError
                loading={(!feedReq && !fError) || (!entities && !eError)}
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
                e.id.startsWith("mat-") &&
                (e.typ.id === "typ-jidlo" || e.typ.id === "typ-luxus") &&
                !automatedResIds.includes(e.id)
        )
        // @ts-ignore
        .sort((a, b) => a.typ.level - b.typ.level);

    let missing =
        Object.values(props.feeding).reduce((a, b) => a + b, 0) -
        feedReq.tokensRequired;

    return (
        <>
            <h1>Krmení týmu {props.team.name}</h1>
            <FormRow label="Parametry krmení">
                <span className="mx-3">Kast: {feedReq.casteCount},</span>{" "}
                <span className="mx-3">
                    Vyžadováno žetonů: {feedReq.tokensRequired}{" "}
                    {missing < 0 && (
                        <span className="font-bold text-red-500">
                            (chybí {-missing})
                        </span>
                    )}
                    ,
                </span>{" "}
                <span className="mx-3">
                    Žetonů na kastu: {feedReq.tokensPerCaste}
                </span>
            </FormRow>
            {["typ-jidlo", "typ-luxus"].map((resType) => (
                <div key={resType}>
                    <h2>{resType === "typ-jidlo" ? "Jídlo" : "Luxus"}</h2>
                    {automatedRes
                        .filter(([r, recommended]: any) => r.typ.id === resType)
                        .map(([r, recommended]: any) => (
                            <FormRow
                                key={r.id}
                                label={
                                    <>
                                        <EntityTag id={r.id} /> ({r?.typ?.level}
                                        )
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
                                    onChange={(v) =>
                                        props.updateResource(r.id, v)
                                    }
                                />
                            </FormRow>
                        ))}
                    {remaingRes
                        .filter((r) => r?.typ?.id === resType)
                        .map((r) => (
                            <FormRow
                                key={r.id}
                                label={
                                    <>
                                        <EntityTag id={r.id} /> ({r?.typ?.level}
                                        )
                                    </>
                                }
                            >
                                <SpinboxInput
                                    value={_.get(props.feeding, r.id, 0)}
                                    onChange={(v) =>
                                        props.updateResource(r.id, v)
                                    }
                                />
                            </FormRow>
                        ))}
                </div>
            ))}
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
    const [action, setAction] = useAtom(urlMapActionAtom);

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
                setAction(MapActiontype.none);
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
    const [action, setAction] = useAtom(urlMapActionAtom);

    if (!availableProductions) {
        return (
            <LoadingOrError
                loading={!availableProductions && !error}
                error={error}
                message="Něco se nepovedlo"
            />
        );
    }

    let food = Object.values(availableProductions).filter(
        (a: any) => a?.typ?.id === "typ-jidlo" || a?.typ?.id == "typ-luxus"
    );

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
                setAction(MapActiontype.none);
            }}
        />
    );
}
