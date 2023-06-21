import { useState } from "react";
import { toast } from "react-toastify";
import useSWR from "swr";
import { Button, LoadingOrError } from "../elements";
import { EntityTag } from "../elements/entities";
import { NeutralMessage } from "../elements/messages";
import { useArmyStates, useMapTileStates } from "../elements/states";
import { MapTileId, TeamId } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { ArmyName } from "./map";

enum DiffType {
    richness = "richness",
    armyLevel = "armyLevel",
    armyMove = "armyMove",
    armyCreate = "armyCreate",
}

export interface MapDiff {
    id: number;
    createdAt: string | Date;
    type: DiffType;
    tile?: MapTileId;
    newRichness?: number;
    newLevel?: number;
    team?: TeamId;
    armyName?: string;
}

export function MapDiffView() {
    return (
        <>
            <div className="flex min-h-screen flex-col bg-gray-100 font-sans leading-normal tracking-normal">
                <div className="mx-auto w-full flex-grow pt-1">
                    <div className="mb-16 w-full px-2 py-10 leading-normal text-gray-800 md:mt-2 md:px-0">
                        <div className="container mx-auto">
                            <MapDiffContent />
                        </div>
                    </div>
                </div>

                <footer className="border-t border-gray-400 bg-white shadow">
                    <div className="container mx-auto flex max-w-md py-8"></div>
                </footer>
            </div>
        </>
    );
}

function MapDiffContent() {
    const {
        data: pendingUpdates,
        error,
        mutate,
    } = useSWR<MapDiff[]>("/game/mapupdates/", fetcher, {
        refreshInterval: 10 * 1000,
    });
    if (!pendingUpdates)
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    return (
        <>
            <h1>Aktualizace mapy</h1>
            {pendingUpdates.length == 0 ? (
                <NeutralMessage>Nejsou žádné aktualizace mapy</NeutralMessage>
            ) : (
                pendingUpdates.map((u) => (
                    <MapUpdate mapUpdate={u} key={u.id} onUpdate={mutate} />
                ))
            )}
            <h1>Stav mapy</h1>
            <MapState />
        </>
    );
}

function UpdateInstructions(props: { mapUpdate: MapDiff }) {
    switch (props.mapUpdate.type) {
        case DiffType.richness:
            return (
                <div>
                    Změň úrodnost pole{" "}
                    <EntityTag id={props.mapUpdate.tile ?? "-"} /> na{" "}
                    {props.mapUpdate.newRichness ?? "-"}.
                </div>
            );

        case DiffType.armyLevel:
            return (
                <div>
                    Zvyš úroveň armády {props.mapUpdate.armyName ?? "-"} týmu{" "}
                    <EntityTag id={props.mapUpdate.team ?? "-"} /> na{" "}
                    {props.mapUpdate.newLevel ?? "-"}.
                </div>
            );
        case DiffType.armyMove:
            return (
                <div>
                    Přesuň armádu <EntityTag id={props.mapUpdate.team ?? "-"} />
                    -{props.mapUpdate.armyName ?? "-"} na{" "}
                    {props.mapUpdate.tile ? (
                        <EntityTag id={props.mapUpdate.tile} />
                    ) : (
                        "domovské pole"
                    )}
                    .
                </div>
            );
        case DiffType.armyCreate:
            return (
                <div>
                    Vytvoř armádu {props.mapUpdate.armyName ?? "-"} týmu{" "}
                    <EntityTag id={props.mapUpdate.team ?? "-"} /> na{" "}
                    {props.mapUpdate.tile ? (
                        <EntityTag id={props.mapUpdate.tile} />
                    ) : (
                        "domovském poli"
                    )}{" "}
                    s úrovní {props.mapUpdate.newLevel ?? "-"}.
                </div>
            );
        default:
            const exhaustiveCheck: never = props.mapUpdate.type;
            return <></>; // For invalid Enum value
    }
}

function MapUpdate(props: { mapUpdate: MapDiff; onUpdate: () => void }) {
    const [deleting, setDeleting] = useState(false);
    const [deleted, setDeleted] = useState(false);

    const handleFinish = () => {
        setDeleting(true);
        axiosService
            .delete(`/game/mapupdates/${props.mapUpdate.id}/`)
            .then(() => {
                props.onUpdate();
                setDeleted(true);
            })
            .catch((error) => {
                console.error("Delete map updates:", error);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            })
            .finally(() => {
                setDeleting(false);
            });
    };

    if (deleted) {
        return null;
    }

    return (
        <div className="orange-500 mb-4 flex w-full rounded-b border-t-4 border-orange-500 bg-orange-200 px-4 py-3 shadow-md">
            <div className="flex-1 text-lg">
                <UpdateInstructions mapUpdate={props.mapUpdate} />
            </div>
            <div className="flex-none align-middle text-sm">
                {new Date(props.mapUpdate.createdAt).toLocaleString("cs-CZ", {
                    weekday: "long",
                    hour: "2-digit",
                    minute: "2-digit",
                })}
            </div>
            <Button
                label={deleting ? "Odesílám " : "Hotovo"}
                className="flex-none align-middle"
                onClick={handleFinish}
                disabled={deleting}
            />
        </div>
    );
}

function MapState() {
    const config = {
        refreshInterval: 10 * 1000,
    };
    const { tiles, error: tError } = useMapTileStates(config);
    const { armies, error: aError } = useArmyStates(config);

    console.log("Armies:", armies);

    if (!tiles || !armies) {
        return (
            <LoadingOrError
                error={tError || aError}
                message="Něco se pokazilo"
            />
        );
    }

    const sortedTiles = tiles.sort((a, b) => a.name.localeCompare(b.name));

    return (
        <div className="relative overflow-x-auto shadow-md sm:rounded-lg">
            <table className="w-full text-left text-sm text-gray-500 dark:text-gray-400">
                <thead className="bg-gray-50 text-xs uppercase text-gray-700 dark:bg-gray-700 dark:text-gray-400">
                    <tr>
                        <th scope="col" className="px-6 py-3 text-right">
                            Políčko
                        </th>
                        <th scope="col" className="px-6 py-3 text-center">
                            Úrodnost
                        </th>
                        <th scope="col" className="px-6 py-3">
                            Budovy
                        </th>
                        <th scope="col" className="px-6 py-3">
                            Armáda
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {sortedTiles.map((t) => {
                        const tileArmies = armies.find(
                            (x) => x.tile === t.entity
                        );
                        return (
                            <tr
                                key={t.entity}
                                className="border-b bg-white dark:border-gray-700 dark:bg-gray-800"
                            >
                                <th
                                    scope="row"
                                    className="whitespace-nowrap px-6 py-4 text-right font-medium text-gray-900 dark:text-white"
                                >
                                    <EntityTag id={t.entity} />
                                </th>
                                <td className="px-6 py-4 text-center">
                                    {t.richnessTokens}
                                </td>
                                <td className="px-6 py-4">
                                    <ul className="list-disc">
                                        {t.buildings.map((b) => (
                                            <li>
                                                <EntityTag id={b} />
                                            </li>
                                        ))}
                                    </ul>
                                </td>
                                <td className="px-6 py-4">
                                    {armies
                                        .filter((x) => x.tile === t.entity)
                                        .map((army) => {
                                            return (
                                                <div className="mx-1">
                                                    Armáda{" "}
                                                    <ArmyName army={army} />{" "}
                                                    týmu{" "}
                                                    <EntityTag id={army.team} />
                                                </div>
                                            );
                                        })}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
