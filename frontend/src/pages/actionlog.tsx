import { useAtom } from "jotai";
import { atomWithHash } from "jotai/utils";
import _ from "lodash";
import { useState } from "react";
import AceEditor from "react-ace";
import useSWR from "swr";
import { Button, CiviMarkdown, LoadingOrError } from "../elements";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";

export const pageAtom = atomWithHash<number>("page", 1);
export const pageSizeAtom = atomWithHash<number>("page_size", 100);

enum InteractionType {
    initiate = "initiate",
    commit = "commit",
    revert = "revert",
}

interface Interaction {
    id: number;
    phase: InteractionType;
    author?: string;
    created: Date | string;
    action: number;
    actionObject: any;
    trace: string;
    new_state: number;
}

interface Action {
    id: number;
    actionType: string;
    entitiesRevision: number;
    description?: string;
    args: any;
    interactions: Interaction[];
}

export function ActionLog() {
    useHideMenu();

    const [page, setPage] = useAtom(pageAtom);
    const [pageSize, setPageSize] = useAtom(pageSizeAtom);
    const { data: actions, error } = useSWR<{
        count: number;
        results: Action[];
        next?: string;
        previous?: string;
    }>(`game/actions/logs?page=${page}&page_size=${pageSize}`, fetcher);

    if (_.isNil(actions)) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    }

    const pageCount = _.ceil(actions.count / pageSize);

    return (
        <>
            <div className="my-2 justify-between md:flex md:items-center">
                <div className="mx-4">
                    <h1 className="my-2">Log akcí</h1>
                    <div className="mx-2 w-full text-sm text-gray-400">
                        zobrazeno {actions.results.length} z {actions.count}{" "}
                        akcí
                    </div>
                </div>
                <div className="mx-4 md:flex md:items-center">
                    <div className="py-1">
                        <label className="mb-1 block w-full pr-4 md:mb-0 md:text-right">
                            Počet akcí na stránku:
                        </label>
                    </div>
                    <div className="field flex flex-wrap">
                        <select
                            className="select"
                            value={pageSize}
                            onChange={(e) =>
                                setPageSize(parseInt(e.target.value))
                            }
                        >
                            {[20, 50, 100, 200].map((size, i) => (
                                <option key={i} value={size}>
                                    {size}
                                </option>
                            ))}
                        </select>{" "}
                    </div>
                </div>
            </div>
            {actions.results.map((a, i) => (
                <ActionView action={a} key={i} />
            ))}
            <div className="flex w-full align-middle">
                <Button
                    className="w-1/3"
                    label="Novější akce"
                    disabled={_.isNil(actions.previous)}
                    onClick={() => setPage(page - 1)}
                />
                <div className="m-auto w-1/3 text-center align-middle">
                    Aktuální strana {page}/{pageCount}
                </div>
                <Button
                    className="w-1/3"
                    label="Starší akce"
                    disabled={_.isNil(actions.next)}
                    onClick={() => setPage(page + 1)}
                />
            </div>
        </>
    );
}

function ActionView(props: { action: Action }) {
    const action = props.action;
    const [expanded, setExpanded] = useState(false);

    console.log("Action log:", action);
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
                            {action.interactions.map((i, k) => (
                                <InteractionView interaction={i} key={k} />
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function InteractionView(props: { interaction: Interaction }) {
    return (
        <div className="row my-1 rounded bg-gray-200 p-2">
            <div>Typ: {props.interaction.phase}</div>
            <AceEditor
                mode="javascript"
                theme="github"
                readOnly={true}
                name="interactioneditor"
                fontSize={14}
                showPrintMargin={true}
                showGutter={true}
                highlightActiveLine={true}
                value={JSON.stringify(props.interaction.actionObject, null, 4)}
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
            <CiviMarkdown>{props.interaction.trace}</CiviMarkdown>
        </div>
    );
}
