import classNames from "classnames";
import { useAtom } from "jotai";
import { atomWithHash } from "jotai/utils";
import { useState } from "react";
import useSWR from "swr";
import {
    Button,
    Dialog,
    FormRow,
    LoadingOrError,
    SpinboxInput,
} from "../elements";
import { PerformAction } from "../elements/action";
import { EntityTag } from "../elements/entities";
import { TileSelect } from "../elements/map";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import { Team } from "../types";
import { fetcher } from "../utils/axios";

export function MapMenu() {
    return null;
}

export const ARMY_GOALS = {
    0: "Okupovat",
    1: "Eliminovat",
    2: "Zásobování",
    3: "Nahradit",
};

enum MapActiontype {
    none = 0,
    building = 1,
    feeding = 2,
    army = 3,
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
    const { team, setTeam, loading, error } = useTeamFromUrl();
    const [action, setAction] = useAtom(urlMapActionAtom);

    if (loading) {
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
                <TeamSelector onChange={handleTeamChange} active={team} />
            </FormRow>
            {team ? (
                <>
                    <FormRow label="Vyberte akci:">
                        <div className="mx-0 w-1/3 flex-initial px-1">
                            <Button
                                label="Krmit"
                                className="mx-0 w-full bg-green-600 hover:bg-green-700"
                                onClick={() => setAction(MapActiontype.feeding)}
                            />
                        </div>
                        <div className="mx-0 w-1/3 flex-initial px-1">
                            <Button
                                label="Armáda"
                                className="mx-0 w-full bg-orange-600 hover:bg-orange-700"
                                onClick={() => setAction(MapActiontype.army)}
                            />
                        </div>
                        <div className="mx-0 w-1/3 flex-initial px-1">
                            <Button
                                label="Stavět"
                                className="w-full"
                                onClick={() =>
                                    setAction(MapActiontype.building)
                                }
                            />
                        </div>
                    </FormRow>
                    <TeamRowIndicator team={team} />

                    {action == MapActiontype.army ? (
                        <ArmyManipulation team={team} />
                    ) : null}
                    {action == MapActiontype.building ? (
                        <BuildingAgenda team={team} />
                    ) : null}
                    {action == MapActiontype.feeding ? (
                        <FeedingAgenda team={team} />
                    ) : null}
                </>
            ) : null}
        </>
    );
}

export function BuildingAgenda(props: { team: Team }) {
    return (
        <>
            <h1>Stavění budovy pro tým {props.team.name}</h1>
        </>
    );
}

export function ArmyManipulation(props: { team: Team; onFinish?: () => void }) {
    const { data: armies, error: armyError } = useSWR<Record<number, any>>(
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
                    <ArmyBadge key={a.prestige} team={props.team} army={a} />
                ))}
            </div>
        </>
    );
}

function ArmyBadge(props: { team: Team; army: any }) {
    const [selectedAction, setSelectedAction] = useState("");

    let className = classNames(
        "bg-white rounded p-4 mx-4 my-4 cursor-pointer shadow-lg flex flex-wrap md:flex-1"
    );

    let attributes = {
        Prestiž: props.army.prestige,
        Vybavení: props.army.equipment,
        Boost: props.army.boost,
        "Stojí na": props.army.tile ? (
            <EntityTag id={props.army.tile} />
        ) : (
            "Nikde"
        ),
        Stav: props.army.state,
        Cíl: props.army.goal,
    };

    let ActionForm: any = {
        armyDeploy: ArmyDeployForm,
        armyRetreat: ArmyRetreatForm,
        armyBoost: ArmyBoostForm,
    }[selectedAction];

    return (
        <div className={className}>
            <div className="w-full md:w-2/3">
                <table className="w-full table-fixed">
                    <tbody>
                        {Object.entries(attributes).map(([k, v]) => (
                            <tr key={k}>
                                <td className="pr-3 text-right font-bold">
                                    {k}:{" "}
                                </td>
                                <td className="text-left">{v}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="w-full px-3 md:w-1/3">
                <Button
                    label="Vyslat armádu"
                    className="my-2 w-full bg-orange-600 hover:bg-orange-700"
                    onClick={() => setSelectedAction("armyDeploy")}
                />
                <Button
                    label="Stáhnout armádu"
                    className="my-2 w-full bg-green-600 hover:bg-green-700"
                    onClick={() => setSelectedAction("armyRetreat")}
                />
                <Button
                    label="Podpořit armádu"
                    className="my-2 w-full bg-blue-600 hover:bg-blue-700"
                    onClick={() => setSelectedAction("armyBoost")}
                />
            </div>
            {ActionForm ? (
                <ActionForm
                    team={props.team}
                    army={props.army}
                    onFinish={() => setSelectedAction("")}
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

    let argsValid = true;
    if (!tile && equipment <= 0)
        argsValid = false;
    return (
        <Dialog onClose={props.onFinish}>
            <PerformAction
                actionName={`Vyslat armádu ${props.army.prestige} týmu ${props.team.name}`}
                actionId="ActionArmyDeploy"
                actionArgs={{
                    team: props.team.id,
                    army: `${props.team.id},${props.army.prestige}`,
                    tile: tile?.id,
                    goal: goal,
                    equipment: equipment,
                    friendlyTeam: friendlyTeam?.id
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
                team={props.team}
                argsValid={argsValid}
                extraPreview={
                    <>
                        <h1>Zadejte extra parametry</h1>
                        <FormRow label="Cílová destinace" error={!tile ? "Je třeba vyplnit" : null}>
                            <TileSelect value={tile} onChange={setTile} />
                        </FormRow>
                        <FormRow label="Mód vyslání">
                            <select
                                className="select"
                                value={goal}
                                onChange={(e) => setGoal(parseInt(e.target.value))}
                            >
                                {Object.entries(ARMY_GOALS).map(([k, v]) => (
                                    <option key={k} value={k}>
                                        {v}
                                    </option>
                                ))}
                            </select>
                        </FormRow>
                        <FormRow label="Vyberte výbavu:" error={equipment <= 0 ? "Výbava nesmí být záporná" : null}>
                            <SpinboxInput
                                value={equipment}
                                onChange={setEquipment}
                            />
                        </FormRow>
                        <FormRow label="Spřátelený tým:">
                            <TeamSelector
                                allowNull
                                active={friendlyTeam}
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
                actionName={`Stáhnout armádu ${props.army.prestige} týmu ${props.team.name}`}
                actionId="ActionRetreat"
                actionArgs={{
                    team: props.team.id,
                    prestige: props.army.prestige,
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
                team={props.team}
            />
        </Dialog>
    );
}

function ArmyBoostForm(props: { team: Team; army: any; onFinish: () => void }) {
    const [boost, setBoost] = useState<number>(0);

    return (
        <Dialog onClose={props.onFinish}>
            <PerformAction
                actionName={`Podpořit armádu ${props.army.prestige} týmů ${props.team.name}`}
                actionId="ActionBoost"
                actionArgs={{
                    team: props.team.id,
                    prestige: props.army.prestige,
                    boost: boost,
                }}
                onFinish={props.onFinish}
                onBack={props.onFinish}
                team={props.team}
                extraPreview={
                    <>
                        <h1>Zadejte extra parametry</h1>
                        <FormRow label="Vyberte boost:">
                            <SpinboxInput value={boost} onChange={setBoost} />
                        </FormRow>
                    </>
                }
            />
        </Dialog>
    );
}

export function FeedingAgenda(props: { team: Team }) {
    return (
        <>
            <h1>Krmení týmu {props.team.name}</h1>
        </>
    );
}
