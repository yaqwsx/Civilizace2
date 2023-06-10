import { useState } from "react";
import AceEditor from "react-ace";
import useSWR from "swr";
import { Button, CiviMarkdown, LoadingOrError } from "../elements";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";

export function ActionLog() {
    useHideMenu();

    const [page, setPage] = useState(0);
    const { data, error } = useSWR<any>(`game/actions/logs?${page}`, fetcher);

    if (!data) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    }

    const { count: pageCount, results: actions } = data;

    return (
        <>
            {actions.map((a: any) => (
                <Action action={a} key={a.id} />
            ))}
            <div className="flex w-full align-middle">
                <Button
                    className="w-1/3"
                    label="Novější akce"
                    disabled={page <= 0}
                    onClick={() => setPage(page - 1)}
                />
                <div className="w-1/3 text-center align-middle">
                    Aktuální strana {page + 1}/{pageCount}
                </div>
                <Button
                    className="w-1/3"
                    label="Starší akce"
                    disabled={page + 1 >= pageCount}
                    onClick={() => setPage(page + 1)}
                />
            </div>
        </>
    );
}

function Action(props: { action: any }) {
    const action = props.action;
    const [expanded, setExpanded] = useState(false);

    console.log(action);
    let author = action.interactions[0].author;
    let entryDate = new Date(
        action.interactions[action.interactions.length - 1].created
    );

    return (
        <div className="my-4 w-full cursor-pointer rounded bg-white py-2 px-4">
            <h3 onClick={() => setExpanded(!expanded)}>
                {expanded ? "▾" : "▸"} {action.id}: {action.description}{" "}
                <span className="text-sm font-normal text-gray-500">
                    ({action.actionType} {author && <>, zadal {author}</>},{" "}
                    {entryDate.toLocaleString("cs-CZ", {
                        weekday: "long",
                        hour: "2-digit",
                        minute: "2-digit",
                    })}
                    )
                </span>
            </h3>
            {expanded && (
                <>
                    <div className="row flex">
                        <div className="w-1/2">
                            <h4 className="font-bold">Parametry</h4>
                            <AceEditor
                                mode="javascript"
                                theme="github"
                                readOnly={true}
                                name="actioneditor"
                                fontSize={14}
                                showPrintMargin={true}
                                showGutter={true}
                                highlightActiveLine={true}
                                value={JSON.stringify(action.args, null, 4)}
                                className="max-h-full w-full"
                                maxLines={10}
                                setOptions={{
                                    enableBasicAutocompletion: false,
                                    enableLiveAutocompletion: false,
                                    enableSnippets: false,
                                    showLineNumbers: false,
                                    tabSize: 4,
                                }}
                            />
                        </div>
                        <div className="w-1/2">
                            <h4 className="font-bold">Interakce</h4>
                            {action.interactions.map((i: any, k: any) => (
                                <Interaction interaction={i} key={k} />
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function interactionName(id: number) {
    const NAMES = ["initiate", "commit", "revert"];

    if (id < 0 || id >= NAMES.length) return `Unknown interaction id ${id}`;
    return NAMES[id];
}

function Interaction(props: { interaction: any }) {
    const intr = props.interaction;
    return (
        <div className="row my-1 rounded bg-gray-200 p-2">
            <div>Typ: {interactionName(intr.phase)}</div>
            <AceEditor
                mode="javascript"
                theme="github"
                readOnly={true}
                name="interactioneditor"
                fontSize={14}
                showPrintMargin={true}
                showGutter={true}
                highlightActiveLine={true}
                value={JSON.stringify(intr.actionObject, null, 4)}
                className="w-full"
                maxLines={10}
                setOptions={{
                    enableBasicAutocompletion: false,
                    enableLiveAutocompletion: false,
                    enableSnippets: false,
                    showLineNumbers: false,
                    tabSize: 4,
                }}
            />
            <CiviMarkdown>{intr.trace}</CiviMarkdown>
        </div>
    );
}
