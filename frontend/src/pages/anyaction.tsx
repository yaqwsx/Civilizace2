import { Ace } from "ace-builds";
import produce from "immer";
import { useAtom } from "jotai";
import { RESET, atomWithHash } from "jotai/utils";
import _ from "lodash";
import { useEffect, useState } from "react";
import AceEditor from "react-ace";
import useSWRImmutable from "swr/immutable";
import {
    Button,
    ComponentError,
    DecimalSpinboxInput,
    FormRow,
    InlineSpinner,
    LoadingOrError,
    SpinboxInput,
} from "../elements";
import { PerformAction, PerformNoInitAction } from "../elements/action";
import { EntityTag, useEntities } from "../elements/entities";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    BuildingEntity,
    BuildingUpgradeEntity,
    DieEntity,
    EntityBase,
    GameState,
    MapTileEntity,
    ResourceEntity,
    ServerActionType,
    ServerArgTypeInfo,
    ServerTypeInfo,
    Team,
    TeamAttributeEntity,
    TechEntity,
    VyrobaEntity,
} from "../types";
import { stringAtomWithHash } from "../utils/atoms";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";

const urlActionAtom = stringAtomWithHash("action");

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

// Confirms to backend/game/viewsets/entity.py:EntityViewSet
// Key is lowercase entity type
function UseAllEntitiesByType() {
    return {
        resource: useEntities<ResourceEntity>("resources"),
        tech: useEntities<TechEntity>("techs"),
        vyroba: useEntities<VyrobaEntity>("vyrobas"),
        maptileentity: useEntities<MapTileEntity>("tiles"),
        building: useEntities<BuildingEntity>("buildings"),
        buildingupgrade:
            useEntities<BuildingUpgradeEntity>("building_upgrades"),
        teamattribute: useEntities<TeamAttributeEntity>("team_attributes"),
        die: useEntities<DieEntity>("dice"),
    };
}

function PrintArgType(type: ServerTypeInfo): string {
    return (
        type.type +
        (type.subtypes ? `[${type.subtypes.map(PrintArgType).join(",")}]` : "")
    );
}

function UnknownArgTypeForm(serverInfo: ServerTypeInfo, error?: string) {
    return (props: ArgumentFormProps) => (
        <>
            <p>
                Expected type: {PrintArgType(serverInfo)}
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

type EntitiesByType = Record<
    string,
    { data?: Record<string, EntityBase>; error?: any }
>;

type ArgFormProps = {
    serverInfo: ServerArgTypeInfo;
    entities: EntitiesByType;
};

function GetArgForm(props: ArgFormProps) {
    switch (props.serverInfo.type.toLowerCase()) {
        case "decimal":
            return (p: ArgumentFormProps) => (
                <DecimalSpinboxInput
                    onChange={p.onChange}
                    value={p.value ?? ""}
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
        case "teamentity":
            return (p: ArgumentFormProps) => (
                <TeamSelector
                    allowNull={!props.serverInfo.required}
                    activeId={p.value}
                    onChange={(team) => p.onChange(team?.id)}
                />
            );
        case "gamestate": {
            const fetchState = (props: {
                setState: (state: GameState) => void;
                setError: (error: string) => void;
            }) => {
                props.setError("Loading current state");
                fetcher<GameState>("/game/state/latest")
                    .then((data) => {
                        props.setState(data);
                    })
                    .catch((error) => {
                        console.error("Couldn't fetch state:", error);
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
            if (_.isNil(props.serverInfo.values)) {
                console.error("Empty values in enum:", props.serverInfo);
                return UnknownArgTypeForm(props.serverInfo);
            }
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
                    {Object.entries(props.serverInfo.values ?? {}).map(
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
            if (props.serverInfo.subtypes?.length !== 2) {
                console.error(
                    "Incorrect subtypes in dict (expected 2 subtypes):",
                    props.serverInfo
                );
                return UnknownArgTypeForm(props.serverInfo);
            }
            const [keyType, valueType] = props.serverInfo.subtypes;

            const keyInfo = GetArgInfo({
                serverInfo: { ...keyType, required: true },
                entities: props.entities,
            });
            const valueInfo = GetArgInfo({
                serverInfo: { ...valueType, required: true },
                entities: props.entities,
            });

            const keyDisplay = (key: any) => {
                const keyTypeName = keyType.type.toLowerCase();
                if (
                    !_.isNil(props.entities[keyTypeName]) ||
                    keyTypeName === "teamentity"
                ) {
                    console.assert(
                        _.isNil(keyType.values),
                        "Unexpect values with entity type",
                        keyType
                    );
                    return <EntityTag id={key} />;
                }
                if (!_.isNil(keyType.values)) {
                    return keyType.values[key];
                }
                if (keyTypeName in ["str", "int", "decimal", "bool"]) {
                    return key;
                }
                return;
            };

            return (p: ArgumentFormProps) => (
                <DictArgForm
                    value={p.value}
                    keyInfo={keyInfo}
                    valueInfo={valueInfo}
                    keyDisplay={keyDisplay}
                    onChange={p.onChange}
                />
            );
        }
        default: {
            const argEntities =
                props.entities[props.serverInfo.type.toLowerCase()];
            if (!_.isNil(argEntities)) {
                const { data, error } = argEntities;

                if (!data) {
                    const errorStr =
                        `Could not load entities` + error ? `: ${error}` : "";
                    return UnknownArgTypeForm(props.serverInfo, errorStr);
                }

                return (p: ArgumentFormProps) => (
                    <select
                        className="select field"
                        value={p.value ?? ""}
                        onChange={(e) =>
                            p.onChange(e.target.value || undefined)
                        }
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

            console.warn(
                "Unknown arg type:",
                props.serverInfo.type.toLowerCase(),
                props.serverInfo
            );
            return UnknownArgTypeForm(props.serverInfo);
        }
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
    keyDisplay: (key: any) => any;
    onChange: (value: any) => void;
}) {
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [newKeyValue, setNewKeyValue] = useState<any>(props.keyInfo.default);
    const [newKeyError, setNewKeyError] = useState<string>();

    const valueDict = props.value ?? {};
    if (!_.isObject(valueDict)) {
        console.error("Value dict is not object or nil:", valueDict);
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

    const addNewKey = (key: any) => {
        updateKeyValue(key, props.valueInfo.default);
    };
    const updateKeyValue = (key: any, value: any) => {
        console.assert(
            _.isString(key),
            "Key has to be string (the dict will be converted to json):",
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
            {Object.entries(valueDict).map(([key, value]) => (
                <FormRow
                    key={key}
                    label={<>{props.keyDisplay(key) || key}:</>}
                    error={errors[key] ?? ""}
                    className="mb-1 flex md:mb-1 md:items-center"
                >
                    <div className="field flex flex-wrap md:w-3/4">
                        {props.valueInfo.form({
                            value: valueDict[key],
                            onChange: (newValue) =>
                                updateKeyValue(key, newValue),
                            onError: (error) => {
                                updateArgError(key, error);
                            },
                        })}
                    </div>
                    <Button
                        label="-"
                        onClick={() => {
                            removeKey(key);
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

export function GetActionTypes(): {
    actions: ActionType[] | undefined;
    error: any;
} {
    const { data: serverActions, error: actionsError } = useSWRImmutable<
        ServerActionType[]
    >(() => "/actions/", fetcher);
    const entities = UseAllEntitiesByType();

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
            >
                <select
                    value={action?.id ?? ""}
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
    const [lastActionId, setLastActionId] = useState<string>();

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

    if (!urlTeam.success) {
        return (
            <LoadingOrError
                error={urlTeam.error}
                message="Nemůžu načíst týmy ze serveru."
            />
        );
    }

    const argsValid = (a: Record<string, any>) => {
        return Object.entries(props.action.args).every(([name, argInfo]) =>
            argInfo.isValid(a[name])
        );
    };

    const handleArgError = (name: string, error?: string) => {
        console.assert(
            _.isObject(argErrors),
            "Arg errors are not object:",
            argErrors
        );
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
        console.assert(_.isObject(args), "Args are not object:", args);
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
        console.assert(_.isObject(args), "Args are not object:", args);
        console.assert(
            _.isObject(argErrors),
            "Arg errors are not object:",
            argErrors
        );

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
    const [parseError, setParseError] = useState<string>();

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
    const [lastValue, setLastValue] = useState<any>();
    const [argsStr, setArgsStr] = useState<string>();
    const [editor, setEditor] = useState<Ace.Editor>();

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
