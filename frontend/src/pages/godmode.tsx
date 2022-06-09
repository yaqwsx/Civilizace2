// @ts-ignore
import { JsonEditor as Editor } from "jsoneditor-react";
import "jsoneditor-react/es/editor.min.css";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Button, Dialog, LoadingOrError } from "../elements";
import { PerformAction } from "../elements/action";
import { fetcher } from "../utils/axios";
import { objectMap } from "../utils/functional";
import AceEditor from "react-ace";

import "ace-builds/webpack-resolver";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "ace-builds/src-noconflict/mode-javascript";
import { useHideMenu } from "./atoms";

export function GodModeMenu() {
    return null;
}

export function GodMode() {
    useHideMenu();

    const {
        data: state,
        error,
        mutate,
    } = useSWR<any>("/game/state/latest", fetcher);
    const [newStateStr, setNewStateStr] = useState<string>("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [editor, setEditor] = useState<any>(undefined);

    useEffect(() => {
        if ((!newStateStr || newStateStr.length == 0) && state)
            setNewStateStr(JSON.stringify(state, undefined, 4));
        if (editor) editor.execCommand("foldall");
    }, [state, editor]);

    if (!state) {
        return (
            <LoadingOrError
                loading={!state && !error}
                error={error}
                message={"Něco se pokazilo"}
            />
        );
    }

    let diff = {
        add: {},
        change: {},
        remove: {},
    };
    if (newStateStr && state) {
        try {
            diff = jsonDiff(JSON.parse(newStateStr), state);
        } catch (e) {}
    }
    console.log(diff);

    return (
        <>
            <h1>God mode</h1>
            {/* <Editor value={state} onChange={setNewState} /> */}

            <AceEditor
                mode="javascript"
                theme="github"
                onChange={setNewStateStr}
                name="godmodeeditor"
                onLoad={setEditor}
                fontSize={14}
                showPrintMargin={true}
                showGutter={true}
                highlightActiveLine={true}
                value={newStateStr}
                className="w-full"
                maxLines={Infinity}
                setOptions={{
                    enableBasicAutocompletion: false,
                    enableLiveAutocompletion: false,
                    enableSnippets: false,
                    showLineNumbers: false,
                    tabSize: 4,
                }}
            />

            <h2 className="mt-10 mb-4">Chcete provést následující změny:</h2>
            <Changelog {...diff} />
            <Button
                className="w-full"
                label="Provést akci"
                onClick={() => setIsSubmitting(true)}
            />
            {isSubmitting && (
                <Dialog onClose={() => setIsSubmitting(false)}>
                    <PerformAction
                        actionName="GodMode"
                        actionId="GodModeAction"
                        actionArgs={{
                            original: state,
                            change: objectMap(diff.change, (v: any) =>
                                JSON.stringify(v)
                            ),
                            add: objectMap(diff.add, (v: any) =>
                                JSON.stringify(v)
                            ),
                            remove: objectMap(diff.remove, (v: any) =>
                                JSON.stringify(v)
                            ),
                        }}
                        onFinish={() => {
                            setIsSubmitting(false);
                            mutate();
                        }}
                        onBack={() => {
                            setIsSubmitting(false);
                        }}
                    />
                </Dialog>
            )}
        </>
    );
}

function Changelog(props: {
    add: Record<string, any>;
    change: Record<string, any>;
    remove: Record<string, any>;
}) {
    return (
        <>
            {Object.keys(props.add).length > 0 && (
                <>
                    <h3>Přidáno</h3>
                    <Changelist items={props.add} />
                </>
            )}
            {Object.keys(props.change).length > 0 && (
                <>
                    <h3>Změněno</h3>
                    <Changelist items={props.change} />
                </>
            )}
            {Object.keys(props.remove).length > 0 && (
                <>
                    <h3>Odebráno</h3>
                    <Changelist items={props.remove} />
                </>
            )}
        </>
    );
}

function Changelist(props: { items: Record<string, any> }) {
    return (
        <ul className="list-disc">
            {Object.entries(props.items).map(([k, v]) => (
                <li key={k}>
                    {k}: {v}
                </li>
            ))}
        </ul>
    );
}

// @ts-ignore
function findNodeInJson(json, path) {
    if (!json || path.length === 0) {
        return { field: undefined, value: undefined };
    }
    const first = path[0];
    const remainingPath = path.slice(1);

    if (remainingPath.length === 0) {
        return {
            field: typeof json[first] !== "undefined" ? first : undefined,
            value: json[first],
        };
    } else {
        return findNodeInJson(json[first], remainingPath);
    }
}

// @ts-ignore
function flattenRec(o, root, result) {
    if (o === null || !(o.constructor == Object)) {
        result[root] = o;
        return;
    }
    Object.keys(o).forEach((key) => {
        var delimiter = root.length != 0 ? "." : "";
        flattenRec(o[key], root + delimiter + key, result);
    });
}

// @ts-ignore
function flatten(o) {
    let result: any[] = [];
    flattenRec(o, "", result);
    return result;
}

// @ts-ignore
function mergeArrays(...arrays) {
    let jointArray: any[] = [];

    arrays.forEach((array) => {
        jointArray = [...jointArray, ...array];
    });
    const uniqueArray = jointArray.reduce((newArray, item) => {
        if (newArray.includes(item)) {
            return newArray;
        } else {
            return [...newArray, item];
        }
    }, []);
    return uniqueArray;
}

function jsonDiff(newJson: any, originalJson: any) {
    var newJ = flatten(newJson);
    var origJ = flatten(originalJson);
    var add: Record<string, any> = {};
    var remove: Record<string, any> = {};
    var change: Record<string, any> = {};
    mergeArrays(Object.keys(newJ), Object.keys(origJ)).forEach((key: any) => {
        if (!(key in newJ)) {
            remove[key] = [origJ[key]];
        } else if (!(key in origJ)) {
            add[key] = [newJ[key]];
        } else if (newJ[key] != origJ[key]) {
            if (Array.isArray(newJ[key])) {
                var newArr = newJ[key];
                var origArr = origJ[key];
                let toAdd = newArr.filter(
                    (x: any) => !origArr.some((y: any) => x == y)
                );
                let toRemove = origArr.filter(
                    (x: any) => !newArr.some((y: any) => x == y)
                );
                if (toAdd.length != 0) {
                    add[key] = toAdd;
                }
                if (toRemove.length != 0) {
                    remove[key] = toRemove;
                }
            } else {
                change[key] = newJ[key];
            }
        }
    });

    return {
        add: add,
        remove: remove,
        change: change,
    };
}
