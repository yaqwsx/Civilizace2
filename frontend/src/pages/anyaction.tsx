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
import { atomWithHash } from "jotai/utils";
import { useState } from "react";
import { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";
import AceEditor from "react-ace";
import { PerformAction, PerformNoInitAction } from "../elements/action";
import { EntityBase, EntityResource, EntityTech, EntityVyroba, ServerActionType, Team } from "../types";
import { useEntities } from "../elements/entities";

const urlActionAtom = atomWithHash<string | undefined>(
    "action",
    undefined,
    {
        serialize: (x) => (x ?? ""),
        deserialize: (x) => (x || undefined),
    }
);

const urlIgnoreCostAtom = atomWithHash<boolean>(
    "igncost",
    false,
    {
        serialize: (x) => (x ? '1' : ''),
        deserialize: (x) => (x === '1'),
    }
);

const urlIgnoreGameStopAtom = atomWithHash<boolean>(
    "igngamestop",
    false,
    {
        serialize: (x) => (x ? '1' : ''),
        deserialize: (x) => (x === '1'),
    }
);

const urlIgnoreThrowsAtom = atomWithHash<boolean>(
    "ignthrows",
    false,
    {
        serialize: (x) => (x ? '1' : ''),
        deserialize: (x) => (x === '1'),
    }
);

type ArgumentFormProps = {
    value: any,
    onChange: (value: any) => void,
};

type ArgumentInfo = {
    isValid: (value: any) => boolean,
    form: (props: ArgumentFormProps) => JSX.Element,
    default?: any
};

export interface ActionType {
    id: string,
    has_init: boolean,
    args: Record<string, ArgumentInfo>,
}

function UnknownArgTypeForm(name: string, serverInfo: { type: string, required: boolean, default?: any }, error?: string) {
    const printType = (type: any) => {
        return type.type + (type.subtypes ? `[${type.subtypes?.map(printType).join(',')}]` : '');
    };

    const typeStr = printType(serverInfo);
    console.log("Unknown arg type", typeStr, { name, serverInfo });

    return (props: ArgumentFormProps) => (
        <>
            <p>Expected type: {typeStr}{error ? ` (${error})` : ''}</p>
            <JsonForm
                onChange={props.onChange}
                value={props.value}
                lines={2}
            />
        </>
    );
}

function GetArgForm(props: {
    name: string,
    serverInfo: { type: string, required: boolean, default?: any },
    entities: Record<string, { data?: Record<string, EntityBase>, loading: boolean, error: any }>,
}) {
    switch (props.serverInfo.type.toLowerCase()) {
        // case 'decimal':
        case 'int':
            return (p: ArgumentFormProps) => (
                <SpinboxInput
                    value={p.value}
                    onChange={p.onChange}
                />
            );
        case 'bool':
            return (p: ArgumentFormProps) => (
                <input
                    className="checkboxinput"
                    type="checkbox"
                    checked={Boolean(p.value)}
                    onChange={(e) => p.onChange(e.target.checked)}
                />
            );
        case 'team':
            {
                const { data, loading, error } = props.entities['team'];

                if (error || loading || data === undefined) {
                    const errorStr = `Could not load teams` + error ? `: ${error}` : '';
                    return UnknownArgTypeForm(props.name, props.serverInfo, errorStr);
                }

                return (p: ArgumentFormProps) => (
                    <TeamSelector
                        allowNull={!props.serverInfo.required}
                        active={data[p.value] as Team}
                        onChange={(team) => p.onChange(team?.id)}
                    />
                );
            }
        case 'maptileentity':
        case 'tech':
        case 'building':
        case 'resource':
        case 'vyroba':
            {
                const { data, loading, error } = props.entities[props.serverInfo.type.toLowerCase()];

                if (error || loading || data === undefined) {
                    const errorStr = `Could not load entities` + error ? `: ${error}` : '';
                    return UnknownArgTypeForm(props.name, props.serverInfo, errorStr);
                }

                return (p: ArgumentFormProps) => (
                    <select
                        className="select field"
                        value={p.value}
                        onChange={(e) => p.onChange(e.target.value || undefined)}
                    >
                        <option value=''>No value</option>
                        {Object.values(data).map((e) => (
                            <option key={e.id} value={e.id}>
                                {e.name}
                            </option>
                        ))}
                    </select>
                );
            }
        case 'enum':
            return (p: ArgumentFormProps) => (
                <select
                    className="select field"
                    value={p.value}
                    onChange={(e) => p.onChange(e.target.value ? Number(e.target.value) : undefined)}
                >
                    <option value=''>No value</option>
                    {Object.entries<any>((props.serverInfo as any).values).map(([name, value]) => (
                        <option key={value} value={value}>
                            {name}
                        </option>
                    ))}
                </select>
            );
        case 'str':
            return (p: ArgumentFormProps) => (
                <input
                    type="text"
                    onChange={p.onChange}
                    value={p.value}
                    className="flex w-full flex-wrap"
                />
            );
        default:
            return UnknownArgTypeForm(props.name, props.serverInfo);
    }
}

function LoadEntitiesByType(): Record<string, { data?: Record<string, EntityBase>, loading: boolean, error: any }> {
    const teams = useTeams();
    return {
        maptileentity: useEntities<EntityBase>('tiles'),
        tech: useEntities<EntityTech>('techs'),
        building: useEntities<EntityBase>('buildings'),
        resource: useEntities<EntityResource>('resources'),
        vyroba: useEntities<EntityVyroba>('vyrobas'),
        team: {
            data: teams.teams ? Object.fromEntries(teams.teams.map((team) => [team.id, team])) : undefined,
            ...teams
        },
    }
}

export function GetActionTypes(): { actions: ActionType[] | undefined, error: any } {
    const { data: serverActions, error: actionsError } = useSWRImmutable<ServerActionType[]>(() => "/actions/", fetcher);
    const entities = LoadEntitiesByType();

    if (serverActions === undefined || actionsError) {
        return { actions: undefined, error: actionsError };
    }

    const actions = serverActions?.map((a) => {
        return {
            ...a,
            args: Object.fromEntries(Object.entries(a.args).map(([name, serverInfo]) => {
                const argInfo: ArgumentInfo = {
                    isValid: (value: any) => !(serverInfo.required && value === undefined),
                    form: GetArgForm({ name, serverInfo, entities }),
                    default: serverInfo.default,
                };
                return [name, argInfo];
            }))
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

    const action = actionId ? actions.find((a) => a.id === actionId) : undefined;
    if (action && action.has_init === noInit) {
        setNoInit(!action.has_init);
    }

    const handleActionIdChange = (value?: string) => {
        setActionId(value);
    }

    const handleNoInitChange = (no_init: boolean) => {
        setNoInit(no_init);
        handleActionIdChange(undefined);
    };

    return (
        <>
            <h1>
                Zadat {action ? `akci ${action.id}` : "libovolnou akci"}
            </h1>
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
            <div className={`w-full rounded h-4 my-4 ${!noInit ? "bg-green-800" : "bg-purple-800"}`} ></div>

            <div className="flex justify-center items-center mb-6">
                <div className="mx-10 field">
                    <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                        Ignore Game Stop:
                    </label>
                    <input
                        className="checkboxinput"
                        type="checkbox"
                        checked={ignoreGameStop}
                        onChange={(e) => setIgnoreGameStop(e.target.checked)}
                    />
                </div>
                {!noInit &&
                    <>
                        <div className="mx-10 field">
                            <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                                Ignore Cost:
                            </label>
                            <input
                                className="checkboxinput"
                                type="checkbox"
                                checked={ignoreCost}
                                onChange={(e) => setIgnoreCost(e.target.checked)}
                            />
                        </div>
                        <div className="mx-10 field">
                            <label className="mb-1 block py-1 pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                                Ignore Throws:
                            </label>
                            <input
                                className="checkboxinput"
                                type="checkbox"
                                checked={ignoreThrows}
                                onChange={(e) => setIgnoreThrows(e.target.checked)}
                            />
                        </div>
                    </>
                }
            </div>

            <h2>Vyberte akci</h2>
            <FormRow label={`Vyber ${!noInit ? "Team Interaction" : "No Init"} akci:`} className="my-8">
                <select
                    value={String(action?.id)}
                    onChange={(event) => handleActionIdChange(event.target.value)}
                    className="select"
                >
                    <option value=''>Vyber akci</option>
                    {actions?.filter((a) => {
                        return a.has_init !== noInit;
                    }).map((a) => {
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
                    onReset={() => setActionId(undefined)}
                    ignoreCost={noInit ? undefined : ignoreCost}
                    ignoreThrows={noInit ? undefined : ignoreThrows}
                    ignoreGameStop={ignoreGameStop}
                    isNoInit={noInit}
                />
            ) : null}
        </>
    );
}


function PerformAnyAction(props: {
    action: ActionType,
    onReset: () => void,
    ignoreCost?: boolean,
    ignoreGameStop?: boolean,
    ignoreThrows?: boolean,
    isNoInit: boolean,
}) {
    const urlTeam = useTeamFromUrl();
    const [args, setArgs] = useState<Record<string, any>>({});
    const [lastActionId, setLastActionId] = useState<string | undefined>(undefined);

    if (lastActionId !== props.action.id) {
        setLastActionId(props.action.id);
        const defaultArgs = Object.fromEntries(Object.entries(props.action.args).map(([name, argInfo]) => [name, argInfo.default]));
        setArgs(defaultArgs);
    }

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

    const isTeamAction = props.action.args['team'] !== undefined;
    const team = isTeamAction ? urlTeam.team : undefined;

    const extraPreview = <>
        {
            isTeamAction ?
                <FormRow
                    label="Argument 'team':"
                    error={props.action.args['team'].isValid(team) ? null : `${team === undefined ? "Chybějící" : "Nevalidní"} argument`}
                >
                    <TeamSelector onChange={urlTeam.setTeam} active={urlTeam.team} allowNull={true} />
                </FormRow>
                : null
        }
        {team ? <TeamRowIndicator team={team} /> : null}
        {
            Object.entries(props.action.args).map(([name, argInfo]) => {
                if (name === "team")
                    return;
                return (
                    <FormRow
                        key={name}
                        label={`Argument '${name}':`}
                        error={argInfo.isValid(args[name]) ? null : `${args[name] === undefined ? "Chybějící" : "Nevalidní"} argument`}
                    >
                        {argInfo.form({
                            value: args[name],
                            onChange: (value: any) => {
                                console.log('Arg change', { name, new_value: value, old_value: args[name] });
                                if (args[name] !== value) {
                                    args[name] = value;
                                    setArgs({ ...args });
                                }
                            }
                        })}
                    </FormRow>
                );
            })
        }
    </>;

    if (props.isNoInit) {
        return <PerformNoInitAction
            actionId={props.action.id}
            actionName={props.action.id + (team ? ` pro tým ${team.name}` : '')}
            actionArgs={{ ...args, team: team?.id }}
            argsValid={(a: Record<string, any>) => Object.entries(props.action.args).every(([name, argInfo]) => argInfo.isValid(a[name]))}
            onBack={props.onReset}
            onFinish={props.onReset}
            ignoreGameStop={props.ignoreGameStop}
            extraPreview={extraPreview}
        />;
    }

    return <PerformAction
        actionId={props.action.id}
        actionName={props.action.id + (team ? ` pro tým ${team.name}` : '')}
        actionArgs={{ ...args, team: team?.id }}
        argsValid={(a: Record<string, any>) => Object.entries(props.action.args).every(([name, argInfo]) => argInfo.isValid(a[name]))}
        onBack={props.onReset}
        onFinish={props.onReset}
        ignoreCost={props.ignoreCost}
        ignoreGameStop={props.ignoreGameStop}
        ignoreThrows={props.ignoreThrows}
        extraPreview={extraPreview}
    />;
}

function JsonForm(props: { value: any, onChange: (value: any) => void, lines?: number }) {
    const [editor, setEditor] = useState<any>(undefined);

    return <AceEditor
        mode="json"
        theme="github"
        onChange={(value: string) => {
            try {
                props.onChange(JSON.parse(value));
            } catch { }
        }}
        name="argeditor"
        onLoad={setEditor}
        fontSize={14}
        showPrintMargin={true}
        showGutter={true}
        highlightActiveLine={true}
        value={JSON.stringify(props.value, undefined, 2)}
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
    />;
}
