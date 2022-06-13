import useSWR from "swr";
import { Button, LoadingOrError } from "../elements";
import { EntityTag } from "../elements/entities";
import { fetcher } from "../utils/axios";

export function MapDiff() {
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

export function MapDiffContent() {
    const {
        data: pendingUpdates,
        error,
        mutate,
    } = useSWR<any[]>("/game/mapupdates", fetcher);
    if (!pendingUpdates)
        return (
            <LoadingOrError
                loading={!pendingUpdates && !error}
                error={error}
                message="Něco se nepovedlo"
            />
        );
    return (
        <>
            <h1>Aktualizace mapy</h1>
            {pendingUpdates.length == 0 ? (
                <>Nejsou žádné aktualizace mapy</>
            ) : (
                pendingUpdates.map((u) => (
                    <MapUpdate mapUpdate={u} key={u.id} onUpdate={mutate} />
                ))
            )}
            <h1>Stav mapy</h1>
            <MapState/>
        </>
    );
}

function MapUpdate(props: { mapUpdate: any; onUpdate: () => void }) {
    return <div className="w-full mb-4 rounded-b border-t-4 px-4 py-3 shadow-md bg-orange-200 border-orange-500 orange-500 flex">
        <div className="flex-1">
        {
            props.mapUpdate.type == 0 && <div>
                Změň úrodnost pole <EntityTag id={props.mapUpdate.tile}/> na {props.mapUpdate.newRichness}.
            </div>
        }
        {
            props.mapUpdate.type == 1 && <div>
                Zvyš úroveň armády {props.mapUpdate.armyName} týmu <EntityTag id={props.mapUpdate.team}/> na {props.mapUpdate.newLevel}.
            </div>
        }
        {
            props.mapUpdate.type == 2 && <div>
                Přesuň armádu {props.mapUpdate.armyName} týmu <EntityTag id={props.mapUpdate.team}/> na {
                    props.mapUpdate.tile ? <EntityTag id={props.mapUpdate.tile}/> : "domovské pole"
                }.
            </div>
        }
        {
            props.mapUpdate.type == 3 && <div>
                Vytvoř armádu {props.mapUpdate.armyName} týmu <EntityTag id={props.mapUpdate.team}/> na {
                    props.mapUpdate.tile ? <EntityTag id={props.mapUpdate.tile}/> : "domovském poli"
                } s úrovní {props.mapUpdate.newLevel}.
            </div>
        }
        </div>
        <Button label="Hotovo" className="flex-none"/>
    </div>
}

function MapState() {
    return <>Tady bude stav mapy</>;
}
