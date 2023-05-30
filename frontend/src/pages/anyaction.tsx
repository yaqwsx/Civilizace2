import useSWRImmutable from "swr/immutable";
import {
    FormRow,
    InlineSpinner,
    ComponentError,
    Button,
    SpinboxInput,
} from "../elements";
import {
    useTeamFromUrl,
    TeamSelector,
    TeamRowIndicator,
    useTeams,
} from "../elements/team";
import { useAtom } from "jotai";
import { RESET, atomWithHash } from "jotai/utils";
import { useEffect, useState } from "react";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";
import AceEditor from "react-ace";
import { PerformAction, PerformNoInitAction } from "../elements/action";
import {
    EntityBase,
    EntityResource,
    EntityTech,
    EntityVyroba,
    ServerActionType,
    Team,
} from "../types";
import { useEntities } from "../elements/entities";
import _ from "lodash";
import { Ace } from "ace-builds";
import produce from "immer";

const urlActionAtom = atomWithHash<string | null>("action", null);

const urlIgnoreCostAtom = atomWithHash<boolean>("igncost", false);
const urlIgnoreGameStopAtom = atomWithHash<boolean>("igngamestop", false);
const urlIgnoreThrowsAtom = atomWithHash<boolean>("ignthrows", false);
const urlJsonArgsAtom = atomWithHash<boolean>("json", false);

type ArgumentFormProps = {
    value: any;
    onChange: (value: any) => void;
    onError: (value: string) => void;
};

type ArgumentInfo = {
    isValid: (value: any) => boolean;
    form: (props: ArgumentFormProps) => JSX.Element;
    default?: any;
};

export interface ActionType {
    id: string;
    has_init: boolean;
    args: Record<string, ArgumentInfo>;
}

function UnknownArgTypeForm(
    serverInfo: { type: string; required: boolean; default?: any },
    error?: string
) {
    const printType = (type: any) => {
        return (
            type.type +
            (type.subtypes
                ? `[${type.subtypes?.map(printType).join(",")}]`
                : "")
        );
    };

    return (props: ArgumentFormProps) => (
        <>
            <p>
                Expected type: {printType(serverInfo)}
                {error ? ` (${error})` : ""}
            </p>
            <JsonForm
                onChange={props.onChange}
                onError={props.onError}
                value={props.value}
                lines={2}
            />
        </>
    );
}

type ArgFormProps = {
    serverInfo: { type: string; required: boolean; default?: any };
    entities: Record<
        string,
        { data?: Record<string, EntityBase>; loading: boolean; error: any }
    >;
};

function GetArgForm(props: ArgFormProps) {
    switch (props.serverInfo.type.toLowerCase()) {
        case "decimal":
            return (p: ArgumentFormProps) => (
                <input
                    type="text"
                    onChange={(e) => {
                        if (/^\d*(\.\d*)?$/.test(e.target.value)) {
                            p.onChange(
                                e.target.value === ""
                                    ? undefined
                                    : e.target.value === "."
                                    ? "0."
                                    : e.target.value
                            );
                        }
                    }}
                    value={p.value ?? ""}
                    placeholder="Decimal"
                    className="flex w-full flex-wrap"
                />
            );
        case "int":
            return (p: ArgumentFormProps) => (
                <SpinboxInput
                    value={p.value}
                    onChange={(value) => {
                        p.onChange(value);
                    }}
                />
            );
        case "bool":
            return (p: ArgumentFormProps) => (
                <input
                    className="checkboxinput"
                    type="checkbox"
                    checked={Boolean(p.value)}
                    onChange={(e) => p.onChange(e.target.checked)}
                />
            );
        case "team":
            return (p: ArgumentFormProps) => (
                <TeamSelector
                    allowNull={!props.serverInfo.required}
                    activeId={p.value}
                    onChange={(team) => p.onChange(team?.id)}
                />
            );
        case "maptileentity":
        case "tech":
        case "building":
        case "resource":
        case "vyroba": {
            const { data, loading, error } =
                props.entities[props.serverInfo.type.toLowerCase()];

            if (error || loading || data === undefined) {
                const errorStr =
                    `Could not load entities` + error ? `: ${error}` : "";
                return UnknownArgTypeForm(props.serverInfo, errorStr);
            }

            return (p: ArgumentFormProps) => (
                <select
                    className="select field"
                    value={p.value ?? ""}
                    onChange={(e) => p.onChange(e.target.value || undefined)}
                >
                    <option value="">No value</option>
                    {Object.values(data).map((e) => (
                        <option key={e.id} value={e.id}>
                            {e.name}
                        </option>
                    ))}
                </select>
            );
        }
        case "gamestate": {
            const fetchState = (props: {
                setState: (state: any) => void;
                setError: (error: string) => void;
            }) => {
                props.setError("Loading current state");
                fetcher("/game/state/latest")
                    .then((data) => {
                        props.setState(data);
                    })
                    .catch((error) => {
                        console.error("Couldn't fetch state", error);
                        props.setError(String(error));
                    });
            };

            return (p: ArgumentFormProps) => (
                <>
                    <p>Expected type: GameState</p>
                    <div className="flex w-full flex-wrap">
                        <div className="mx-0 w-3/4 flex-initial px-1">
                            <JsonForm
                                onChange={p.onChange}
                                onError={p.onError}
                                value={p.value}
                            />
                        </div>
                        <div className="mx-0 flex w-1/4 flex-initial px-1">
                            <Button
                                label="Reload State"
                                className="my-auto mx-auto bg-purple-700 hover:bg-purple-800"
                                onClick={() =>
                                    fetchState({
                                        setState: p.onChange,
                                        setError: p.onError,
                                    })
                                }
                            />
                        </div>
                    </div>
                </>
            );
        }
        case "enum":
            return (p: ArgumentFormProps) => (
                <select
                    className="select field"
                    value={p.value ?? ""}
                    onChange={(e) =>
                        p.onChange(
                            e.target.value ? Number(e.target.value) : undefined
                        )
                    }
                >
                    <option value="">No value</option>
                    {Object.entries<any>((props.serverInfo as any).values).map(
                        ([name, value]) => (
                            <option key={value} value={value}>
                                {name}
                            </option>
                        )
                    )}
                </select>
            );
        case "str":
            return (p: ArgumentFormProps) => (
                <input
                    type="text"
                    onChange={(e) => p.onChange(e.target.value)}
                    value={p.value ?? ""}
                    placeholder="Text"
                    className="flex w-full flex-wrap"
                />
            );
        case "dict": {
            const [keyType, valueType]: { type: string }[] = (
                props.serverInfo as any
            ).subtypes;

            const keyInfo = GetArgInfo({
                serverInfo: { ...keyType, required: true },
                entities: props.entities,
            });
            const valueInfo = GetArgInfo({
                serverInfo: { ...valueType, required: true },
                entities: props.entities,
            });

            return (p: ArgumentFormProps) => (
                <DictArgForm
                    value={p.value}
                    keyInfo={keyInfo}
                    valueInfo={valueInfo}
                    onChange={p.onChange}
                />
            );
        }
        default:
            console.log(
                "Unknown arg type",
                props.serverInfo.type.toLowerCase(),
                props.serverInfo
            );
            return UnknownArgTypeForm(props.serverInfo);
    }
}

function GetArgInfo(props: ArgFormProps): ArgumentInfo {
    return {
        isValid: (value: any) => !(props.serverInfo.required && _.isNil(value)),
        form: GetArgForm(props),
        default: props.serverInfo.default,
    };
}

function DictArgForm(props: {
    keyInfo: ArgumentInfo;
    valueInfo: ArgumentInfo;
    value: any;
    onChange: (value: any) => void;
}) {
    const [errors, setErrors] = useState<Record<string, string | undefined>>(
        {}
    );
    const [newKeyValue, setNewKeyValue] = useState<any>(props.keyInfo.default);
    const [newKeyError, setNewKeyError] = useState<string | undefined>();

    const valueDict = props.value ?? {};
    console.assert(_.isObject(valueDict));
    if (!_.isObject(valueDict)) {
        props.onChange(undefined);
    }

    const updateArgError = (key: string, error?: string) => {
        setErrors(
            produce(errors, (orig) => {
                if (error) {
                    orig[key] = error;
                } else {
                    delete orig[key];
                }
            })
        );
    };

    const addNewKey = (key: any) =>
        updateKeyValue(key, props.valueInfo.default);
    const updateKeyValue = (key: any, value: any) => {
        console.assert(
            _.isString(key),
            "Key has to be string",
            typeof key,
            key
        );
        props.onChange(
            produce(valueDict, (orig: any) => {
                orig[key] = value;
            })
        );
        updateArgError(key, getArgError({ value, argInfo: props.valueInfo }));
    };
    const removeKey = (key: any) => {
        props.onChange(
            produce(valueDict, (orig: any) => {
                delete orig[key];
            })
        );
    };

    return (
        <div className="w-full">
            {Object.entries(valueDict).map(([name, value]) => (
                <FormRow
                    key={name}
                    label={`${name}:`}
                    error={errors[name] ?? ""}
                    className="mb-1 flex md:mb-1 md:items-center"
                >
                    <div className="field flex flex-wrap md:w-3/4">
                        {props.valueInfo.form({
                            value: valueDict[name],
                            onChange: (newValue) =>
                                updateKeyValue(name, newValue),
                            onError: (error) => {
                                updateArgError(name, error);
                            },
                        })}
                    </div>
                    <Button
                        label="-"
                        onClick={() => {
                            removeKey(name);
                        }}
                        className="m-1 bg-red-700 hover:bg-red-800"
                    />
                </FormRow>
            ))}
            <FormRow
                label="New Key:"
                error={newKeyError ?? ""}
                className="mb-1 md:mb-0 md:flex md:items-center"
            >
                <div className="field flex flex-wrap md:w-3/4">
                    {props.keyInfo.form({
                        value: newKeyValue,
                        onChange: (value) => {
                            setNewKeyValue(value);
                            setNewKeyError("");
                        },
                        onError: setNewKeyError,
                    })}
                </div>
                <Button
                    label="+"
                    disabled={
                        _.isNil(newKeyValue) || _.hasIn(valueDict, newKeyValue)
                    }
                    onClick={() => {
                        addNewKey(newKeyValue);
                        setNewKeyValue(props.keyInfo.default);
                    }}
                    className="m-1 bg-green-700 hover:bg-green-800"
                />
            </FormRow>
        </div>
    );
}

function LoadEntitiesByType(): Record<
    string,
    { data?: Record<string, EntityBase>; loading: boolean; error: any }
> {
    const teams = useTeams();
    return {
        maptileentity: useEntities<EntityBase>("tiles"),
        tech: useEntities<EntityTech>("techs"),
        building: useEntities<EntityBase>("buildings"),
        resource: useEntities<EntityResource>("resources"),
        vyroba: useEntities<EntityVyroba>("vyrobas"),
        team: {
            data: teams.teams
                ? Object.fromEntries(teams.teams.map((team) => [team.id, team]))
                : undefined,
            ...teams,
        },
    };
}

export function GetActionTypes(): {
    actions: ActionType[] | undefined;
    error: any;
} {
    const { data: serverActions, error: actionsError } = useSWRImmutable<
        ServerActionType[]
    >(() => "/actions/", fetcher);
    const entities = LoadEntitiesByType();

    if (serverActions === undefined || actionsError) {
        return { actions: undefined, error: actionsError };
    }

    const actions = serverActions?.map((a) => {
        return {
            ...a,
            args: Object.fromEntries(
                Object.entries(a.args).map(([name, serverInfo]) => {
                    return [name, GetArgInfo({ serverInfo, entities })];
                })
            ),
        };
    });

    return { actions, error: undefined };
}

export function AnyAction() {
    useHideMenu();

    const { actions, error: actionsError } = GetActionTypes();
    const [actionId, setActionId] = useAtom(urlActionAtom);
    const [ignoreCost, setIgnoreCost] = useAtom(urlIgnoreCostAtom);
    const [ignoreGameStop, setIgnoreGameStop] = useAtom(urlIgnoreGameStopAtom);
    const [ignoreThrows, setIgnoreThrows] = useAtom(urlIgnoreThrowsAtom);
    const [jsonArgs, setJsonArgs] = useAtom(urlJsonArgsAtom);
    const [noInit, setNoInit] = useState(false);

    if (actionsError) {
        return (
            <ComponentError>
                <p>Nemůžu načíst akce ze serveru.</p>
                <p>{actionsError.toString()}</p>
            </ComponentError>
        );
    }
    if (actions === undefined) {
        return <InlineSpinner />;
    }

    const action = actionId
        ? actions.find((a) => a.id === actionId)
        : undefined;
    if (action && action.has_init === noInit) {
        setNoInit(!action.has_init);
    }

    const handleActionIdChange = (value?: string) => {
        setActionId(value ?? RESET);
    };

    const handleNoInitChange = (no_init: boolean) => {
        setNoInit(no_init);
        handleActionIdChange(undefined);
    };

    return (
        <>
            <h1>Zadat {action ? `akci ${action.id}` : "libovolnou akci"}</h1>
            <FormRow label="Vyberte typ akce:">
                <div className="mx-0 w-1/2 flex-initial px-1">
                    <Button
                        label="Team Interaction"
                        className="mx-0 w-full bg-green-600 hover:bg-green-700"
                        onClick={() => handleNoInitChange(false)}
                    />
                </div>
                <div className="mx-0 w-1/2 flex-initial px-1">
                    <Button
                        label="No Init Action"
                        className="w-full bg-purple-600 hover:bg-purple-700"
                        onClick={() => handleNoInitChange(true)}
                    />
                </div>
            </FormRow>
            <div
                className={`my-4 h-4 w-full rounded ${
                    !noInit ? "bg-green-800" : "bg-purple-800"
                }`}
            ></div>

            <div className="mb-6 flex items-center justify-center">
                <div className="field mx-10">
                    <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                        Ignore Game Stop:
                    </label>
                    <input
                        className="checkboxinput"
                        type="checkbox"
                        checked={ignoreGameStop}
                        onChange={(e) =>
                            setIgnoreGameStop(e.target.checked || RESET)
                        }
                    />
                </div>
                {!noInit && (
                    <>
                        <div className="field mx-10">
                            <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                                Ignore Cost:
                            </label>
                            <input
                                className="checkboxinput"
                                type="checkbox"
                                checked={ignoreCost}
                                onChange={(e) =>
                                    setIgnoreCost(e.target.checked || RESET)
                                }
                            />
                        </div>
                        <div className="field mx-10">
                            <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                                Ignore Throws:
                            </label>
                            <input
                                className="checkboxinput"
                                type="checkbox"
                                checked={ignoreThrows}
                                onChange={(e) =>
                                    setIgnoreThrows(e.target.checked || RESET)
                                }
                            />
                        </div>
                    </>
                )}
                <div className="field mx-10">
                    <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                        Json Args:
                    </label>
                    <input
                        className="checkboxinput"
                        type="checkbox"
                        checked={jsonArgs}
                        onChange={(e) => setJsonArgs(e.target.checked || RESET)}
                    />
                </div>
            </div>

            <h2>Vyberte akci</h2>
            <FormRow
                label={`Vyber ${
                    !noInit ? "Team Interaction" : "No Init"
                } akci:`}
                className="my-8"
            >
                <select
                    value={String(action?.id ?? "")}
                    onChange={(event) =>
                        handleActionIdChange(event.target.value)
                    }
                    className="select"
                >
                    <option value="">Vyber akci</option>
                    {actions
                        ?.filter((a) => {
                            return a.has_init !== noInit;
                        })
                        .map((a) => {
                            return (
                                <option key={a.id} value={a.id}>
                                    {a.id}
                                </option>
                            );
                        })}
                </select>
            </FormRow>

            {action ? (
                <PerformAnyAction
                    action={action}
                    onReset={() => setActionId(RESET)}
                    ignoreCost={noInit ? undefined : ignoreCost}
                    ignoreThrows={noInit ? undefined : ignoreThrows}
                    ignoreGameStop={ignoreGameStop}
                    isNoInit={noInit}
                    jsonArgs={jsonArgs}
                />
            ) : null}
        </>
    );
}

function getArgError(props: {
    value?: any;
    argInfo: ArgumentInfo | undefined;
}) {
    if (props.argInfo === undefined) {
        return _.isNil(props.value) ? undefined : "Neočekávaný argument";
    }
    if (props.argInfo.isValid(props.value)) {
        return undefined;
    }
    return _.isNil(props.value) ? "Chybící argument" : "Nevalidní argument";
}

function PerformAnyAction(props: {
    action: ActionType;
    onReset: () => void;
    ignoreCost?: boolean;
    ignoreGameStop?: boolean;
    ignoreThrows?: boolean;
    isNoInit: boolean;
    jsonArgs?: boolean;
}) {
    const urlTeam = useTeamFromUrl();
    const [args, setArgs] = useState<Record<string, any>>({});
    const [argErrors, setArgErrors] = useState<Record<string, string> | string>(
        {}
    );
    const [lastActionId, setLastActionId] = useState<string | undefined>(
        undefined
    );

    const setDefaultArgs = () => {
        const defaultArgs = Object.fromEntries(
            Object.entries(props.action.args).map(([name, argInfo]) => [
                name,
                name === "team" ? urlTeam.team?.id : argInfo.default,
            ])
        );
        setArgs(defaultArgs);
        setArgErrors(
            Object.fromEntries(
                Object.entries(props.action.args)
                    .filter(
                        ([name, argInfo]) => !argInfo.isValid(defaultArgs[name])
                    )
                    .map(([name, argInfo]) => [
                        name,
                        (_.isNil(defaultArgs[name]) ? "Chybící" : "Nevalidní") +
                            " argument",
                    ])
            )
        );
    };

    useEffect(() => {
        if (props.action.id !== lastActionId) {
            setLastActionId(props.action.id);
            setDefaultArgs();
        }
    }, [props.action.id]);

    const isTeamAction = props.action.args["team"] !== undefined;
    useEffect(() => {
        if (isTeamAction && urlTeam.team?.id !== args["team"]) {
            handleArgChange("team", urlTeam.team?.id);
        }
    }, [urlTeam.team?.id, props.action.id]);

    if (urlTeam.error) {
        return (
            <ComponentError>
                <p>Nemůžu načíst týmy ze serveru.</p>
                <p>{urlTeam.error.toString()}</p>
            </ComponentError>
        );
    }
    if (urlTeam.loading) {
        return <InlineSpinner />;
    }

    const argsValid = (a: Record<string, any>) => {
        return Object.entries(props.action.args).every(([name, argInfo]) =>
            argInfo.isValid(a[name])
        );
    };

    const handleArgError = (name: string, error?: string) => {
        console.assert(_.isObject(argErrors));
        setArgErrors(
            produce(_.isObject(argErrors) ? argErrors : {}, (orig) => {
                if (error) {
                    orig[name] = error;
                } else {
                    delete orig[name];
                }
            })
        );
    };
    const handleArgChange = (name: string, value?: any) => {
        console.assert(_.isObject(args));
        if (args[name] !== value) {
            setArgs(
                produce(args, (orig) => {
                    orig[name] = value;
                })
            );
            handleArgError(
                name,
                getArgError({ value, argInfo: props.action.args[name] })
            );
        }
    };
    const handleTeamArgChange = (team?: Team) => {
        urlTeam.setTeam(team);
        handleArgChange("team", team?.id);
    };
    const handleAllArgsChange = (newArgs: any) => {
        if (!_.isObject(newArgs)) {
            setArgErrors("Arguments json has to be a dict");
            return;
        }

        setArgs(newArgs);
        const newArgErrors: Record<string, string> = {};
        for (var [name, value] of Object.entries(newArgs)) {
            const error = getArgError({
                value,
                argInfo: props.action.args[name],
            });
            if (error) {
                newArgErrors[name] = error;
            }
        }
        for (var name in props.action.args) {
            if ((newArgs as Record<string, any>)[name] === undefined) {
                const error = getArgError({ argInfo: props.action.args[name] });
                if (error) {
                    newArgErrors[name] = error;
                }
            }
        }
        setArgErrors(newArgErrors);
    };

    const team = isTeamAction
        ? urlTeam.allTeams?.find((t) => t.id === args["team"])
        : undefined;

    let extraPreview: JSX.Element;
    if (props.jsonArgs) {
        extraPreview = (
            <AllArgsForm
                args={args}
                argErrors={argErrors}
                onChange={handleAllArgsChange}
            />
        );
    } else {
        console.assert(_.isObject(args));
        console.assert(_.isObject(argErrors));

        extraPreview = (
            <>
                {isTeamAction ? (
                    <>
                        <FormRow
                            label="Argument 'team':"
                            error={getArgError({
                                value: team?.id,
                                argInfo: props.action.args["team"],
                            })}
                        >
                            <TeamSelector
                                onChange={handleTeamArgChange}
                                activeId={team?.id}
                                allowNull={true}
                            />
                        </FormRow>
                        <TeamRowIndicator team={team} />
                    </>
                ) : null}
                {Object.entries(props.action.args).map(([name, argInfo]) => {
                    if (name === "team") return;
                    return (
                        <FormRow
                            key={name}
                            label={`Argument '${name}':`}
                            error={(argErrors as Record<string, any>)[name]}
                        >
                            {argInfo.form({
                                value: args[name],
                                onChange: (value: any) =>
                                    handleArgChange(name, value),
                                onError: (error: string) =>
                                    handleArgError(name, error),
                            })}
                        </FormRow>
                    );
                })}
            </>
        );
    }

    if (props.isNoInit) {
        return (
            <PerformNoInitAction
                actionId={props.action.id}
                actionName={
                    props.action.id + (team ? ` pro tým ${team.name}` : "")
                }
                actionArgs={args}
                argsValid={argsValid}
                onBack={props.onReset}
                onFinish={props.onReset}
                ignoreGameStop={props.ignoreGameStop}
                extraPreview={extraPreview}
            />
        );
    }

    return (
        <PerformAction
            actionId={props.action.id}
            actionName={props.action.id + (team ? ` pro tým ${team.name}` : "")}
            actionArgs={args}
            argsValid={(a: Record<string, any>) =>
                Object.entries(props.action.args).every(([name, argInfo]) =>
                    argInfo.isValid(a[name])
                )
            }
            onBack={props.onReset}
            onFinish={props.onReset}
            ignoreCost={props.ignoreCost}
            ignoreGameStop={props.ignoreGameStop}
            ignoreThrows={props.ignoreThrows}
            extraPreview={extraPreview}
        />
    );
}

function AllArgsForm(props: {
    args: Record<string, any>;
    argErrors: string | Record<string, string>;
    onChange: (value: any) => void;
}) {
    const [parseError, setParseError] = useState<string | undefined>(undefined);

    let jsonArgsError: JSX.Element | undefined;
    if (_.isObject(props.argErrors)) {
        jsonArgsError = (
            <>
                {Object.entries(props.argErrors)
                    .filter(([name, error]) => error)
                    .map(([name, error]) => (
                        <p key={name}>
                            {name}: {error}
                        </p>
                    ))}
            </>
        );
    } else {
        jsonArgsError = <p>{props.argErrors}</p>;
    }

    return (
        <FormRow
            label={`All arguments:`}
            error={
                <>
                    {jsonArgsError}
                    {parseError ? <p className="mt-2">Parse Error</p> : null}
                </>
            }
        >
            <JsonForm
                value={props.args}
                onChange={(value) => {
                    setParseError(undefined);
                    props.onChange(value);
                }}
                onError={setParseError}
            />
        </FormRow>
    );
}

function JsonForm(props: {
    value: any;
    onChange: (value: any) => void;
    onError?: (value: string) => void;
    lines?: number;
}) {
    const [lastValue, setLastValue] = useState<any>(undefined);
    const [argsStr, setArgsStr] = useState<string>("");
    const [editor, setEditor] = useState<Ace.Editor | undefined>(undefined);

    const onError = props.onError ?? (() => {});

    useEffect(() => {
        if (!_.isEqual(props.value, lastValue)) {
            setArgsStr(
                JSON.stringify(
                    props.value,
                    (k, v) => (_.isUndefined(v) ? null : v),
                    2
                )
            );
            setLastValue(props.value);
        }
    }, [props.value]);

    return (
        <AceEditor
            mode="json"
            theme="github"
            onChange={(value: string) => {
                setArgsStr(value);
                try {
                    const parsedValue = JSON.parse(value);
                    setLastValue(parsedValue);
                    props.onChange(parsedValue);
                } catch (e) {
                    onError(String(e));
                }
            }}
            name="argeditor"
            onLoad={setEditor}
            fontSize={14}
            showPrintMargin={true}
            showGutter={true}
            highlightActiveLine={true}
            value={argsStr}
            className="w-full"
            minLines={props.lines}
            maxLines={20}
            setOptions={{
                enableBasicAutocompletion: false,
                enableLiveAutocompletion: false,
                enableSnippets: false,
                showLineNumbers: false,
                tabSize: 4,
            }}
        />
    );
}
