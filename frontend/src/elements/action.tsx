import { useEffect, useState } from "react";
import {
    ActionDiceRequirementsResponse,
    ActionResponse,
    UnfinishedAction,
} from "../types";
import axiosService, { fetcher } from "../utils/axios";

import { toast } from "react-toastify";
import {
    Button,
    CiviMarkdown,
    InlineSpinner,
    LoadingOrError,
    SpinboxInput,
    useFocus,
} from ".";
import {
    ErrorMessage,
    NeutralMessage,
    SuccessMessage,
    WarningMessage,
} from "./messages";

import { useAtom, useSetAtom } from "jotai";
import { RESET, atomWithHash } from "jotai/utils";
import _ from "lodash";
import { Link, Navigate } from "react-router-dom";
import useSWR, { useSWRConfig } from "swr";
import { useElementSize } from "usehooks-ts";
import { useDebounceDeep } from "../utils/react";
import { useTeamWork } from "./entities";
import { PrintStickers } from "./printing";

export const activeActionIdAtom = atomWithHash<number | null>(
    "activeAction",
    null
);
export const finishedActionIdAtom = atomWithHash<number | null>(
    "finishedAction",
    null
);

export function useUnfinishedActions(refreshInterval?: number) {
    const { data: actions, ...other } = useSWR<UnfinishedAction[]>(
        "game/actions/team/unfinished",
        fetcher,
        { refreshInterval }
    );
    const [activeAction] = useAtom(activeActionIdAtom);
    const [finishedAction] = useAtom(finishedActionIdAtom);
    return {
        actions: actions?.filter(
            (a) => a.id !== activeAction && a.id !== finishedAction
        ),
        ...other,
    };
}

export function UnfinishedActionBar() {
    const { actions } = useUnfinishedActions(10000);

    if (!actions || actions.length == 0) return null;
    return (
        <div className="red-500 mb-4 w-full border-t-4 border-red-500 bg-red-200 p-3 shadow-md">
            {actions.map((a) => {
                return (
                    <Link
                        key={a.id}
                        to={`/actions/team/${a.id}`}
                        className="block w-full"
                    >
                        Máte nedokončenou akci {a.id}: {a.description}.
                        Dokončete ji prosím kliknutím.
                    </Link>
                );
            })}
        </div>
    );
}

export function useActionPreview<TArgs>(props: {
    actionId: string;
    actionArgs: TArgs;
    argsValid: (args: TArgs) => boolean;
    ignoreGameStop?: boolean;
    ignoreCost?: boolean;
    ignoreThrows?: boolean;
    isNoInit?: boolean;
}) {
    const [previewResponse, setPreviewResponse] = useState<ActionResponse>();
    const [error, setError] = useState<any>();

    const debounced = useDebounceDeep(
        {
            args: props.actionArgs,
            ignoreCost: props.ignoreCost,
            ignoreGameStop: props.ignoreGameStop,
            ignoreThrows: props.ignoreThrows,
        },
        500
    );

    useEffect(() => {
        setError(undefined);
        setPreviewResponse(undefined);

        if (!props.argsValid(debounced.args)) {
            return;
        }

        axiosService
            .post<ActionResponse>(
                `/game/actions/${props.isNoInit ? "noinit" : "team"}/dry/`,
                {
                    action: props.actionId,
                    args: debounced.args,
                    ignore_cost: debounced.ignoreCost,
                    ignore_game_stop: debounced.ignoreGameStop,
                    ignore_throws: debounced.ignoreThrows,
                }
            )
            .then((data) => {
                setError(undefined);
                setPreviewResponse(data.data);
            })
            .catch((error) => {
                console.error(error);
                setPreviewResponse(undefined);
                setError(error);
            });
    }, [props.actionId, debounced]);

    return {
        previewResponse,
        error,
        debouncedArgs: debounced.args,
    };
}

enum ActionPhase {
    initiatePhase = 0,
    diceThrowPhase = 1,
    finish = 2,
}

export function PerformAction<TArgs>(props: {
    actionName: string | JSX.Element;
    actionId: string;
    actionArgs: TArgs;
    argsValid?: (args: TArgs) => boolean;
    extraPreview?: JSX.Element;
    onFinish: () => void;
    onBack: () => void;
    ignoreCost?: boolean;
    ignoreGameStop?: boolean;
    ignoreThrows?: boolean;
}) {
    const [phase, setPhase] = useState<{
        phase: ActionPhase;
        data?: ActionResponse;
    }>({
        phase: ActionPhase.initiatePhase,
    });
    const setActiveAction = useSetAtom(activeActionIdAtom);

    useEffect(() => {
        return () => {
            setActiveAction(RESET);
        };
    }, []);

    let changePhase = (phase: ActionPhase, data: ActionResponse) => {
        setPhase({
            phase,
            data,
        });
    };

    if (phase.phase == ActionPhase.initiatePhase) {
        return (
            <>
                {props.extraPreview}
                <ActionPreviewPhase
                    actionName={props.actionName}
                    actionId={props.actionId}
                    actionArgs={props.actionArgs}
                    onAbort={props.onBack}
                    changePhase={changePhase}
                    argsValid={props.argsValid ?? (() => true)}
                    ignoreGameStop={props.ignoreGameStop}
                    ignoreCost={props.ignoreCost}
                    ignoreThrows={props.ignoreThrows}
                />
                <div className="my-8 h-1 w-full" />
            </>
        );
    }
    if (phase.phase == ActionPhase.diceThrowPhase) {
        if (!phase.data || _.isNil(phase.data.action)) {
            console.error("Empty data in dice throw phase", phase);
            return (
                <LoadingOrError
                    error={phase || true}
                    message="Cannot load commit data in dice throw phase"
                />
            );
        }
        if (props.ignoreThrows) {
            return (
                <>
                    <IgnoreActionDicePhase
                        actionNumber={phase.data.action}
                        actionName={props.actionName}
                        changePhase={changePhase}
                    />
                    <div className="my-8 h-1 w-full" />
                </>
            );
        } else {
            return (
                <>
                    <ActionDicePhase
                        actionNumber={phase.data.action}
                        message={phase.data.message}
                        actionName={props.actionName}
                        changePhase={changePhase}
                    />
                    <div className="my-8 h-1 w-full" />
                </>
            );
        }
    }

    if (phase.phase == ActionPhase.finish) {
        if (!phase.data) {
            console.error("Empty data in finish phase", phase);
            return (
                <LoadingOrError
                    error={phase || true}
                    message={`Cannot load commit data in finish phase`}
                />
            );
        }
        return (
            <>
                <ActionFinishPhase
                    response={phase.data}
                    actionName={props.actionName}
                    onFinish={props.onFinish}
                />
                <div className="my-8 h-1 w-full" />
            </>
        );
    }

    const exhaustiveCheck: never = phase.phase;
    return (
        <ErrorMessage>
            Toto nemělo nastat. Není to nic vážného, ale až budeš mít chvíli,
            řekni o tom Honzovi
        </ErrorMessage>
    );
}

export function PerformNoInitAction<TArgs>(props: {
    actionName: string | JSX.Element;
    actionId: string;
    actionArgs: TArgs;
    argsValid?: (args: TArgs) => boolean;
    extraPreview?: JSX.Element;
    onFinish: () => void;
    onBack: () => void;
    ignoreGameStop?: boolean;
}) {
    const [actionResponse, setActionResponse] = useState<ActionResponse>();
    const setActiveAction = useSetAtom(activeActionIdAtom);

    useEffect(() => {
        return () => {
            setActiveAction(RESET);
        };
    }, []);

    if (_.isNil(actionResponse)) {
        return (
            <>
                {props.extraPreview}
                <NoInitActionPreviewPhase
                    actionName={props.actionName}
                    actionId={props.actionId}
                    actionArgs={props.actionArgs}
                    onAbort={props.onBack}
                    changePhase={(phase, data) => {
                        console.assert(
                            phase === ActionPhase.finish && data,
                            "Expected finish phase with data",
                            { phase, data }
                        );
                        setActionResponse(data);
                    }}
                    argsValid={props.argsValid ?? (() => true)}
                    ignoreGameStop={props.ignoreGameStop}
                />
                <div className="my-8 h-1 w-full" />
            </>
        );
    }

    return (
        <>
            <ActionFinishPhase
                response={actionResponse}
                actionName={props.actionName}
                onFinish={props.onFinish}
            />
            <div className="my-8 h-1 w-full" />
        </>
    );
}

function NoInitActionPreviewPhase<TArgs>(props: {
    actionName: string | JSX.Element;
    actionId: string;
    actionArgs: TArgs;
    onAbort: () => void;
    changePhase: (phase: ActionPhase, data: ActionResponse) => void;
    argsValid: (args: TArgs) => boolean;
    ignoreGameStop?: boolean;
}) {
    const { previewResponse, error, debouncedArgs } = useActionPreview({
        actionId: props.actionId,
        actionArgs: props.actionArgs,
        argsValid: props.argsValid,
        ignoreGameStop: props.ignoreGameStop,
        isNoInit: true,
    });
    const [lastArgs, setLastArgs] = useState<[string, TArgs]>();
    const [submitting, setSubmitting] = useState(false);
    const [commitResult, setCommitResult] = useState<ActionResponse>();
    const [loaderHeight, setLoaderHeight] = useState(0);
    const [messageRef, { height }] = useElementSize();
    const { mutate } = useSWRConfig();
    const setActiveAction = useSetAtom(activeActionIdAtom);
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    if (height != 0 && height != loaderHeight) {
        setLoaderHeight(height);
    }

    if (!_.isEqual(lastArgs, [props.actionId, props.actionArgs])) {
        setLastArgs([props.actionId, props.actionArgs]);
        setCommitResult(undefined);
    }

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<ActionResponse>("/game/actions/noinit/commit/", {
                action: props.actionId,
                args: props.actionArgs,
                ignore_game_stop: props.ignoreGameStop,
            })
            .then((data) => {
                setSubmitting(false);
                let result = data.data;
                setActiveAction(result?.action ?? RESET);
                if (result.success) {
                    setFinishedAction(result?.action ?? RESET);
                    mutate("/game/actions/team/unfinished");
                    props.changePhase(ActionPhase.finish, result);
                } else {
                    setCommitResult(result);
                    toast.error(
                        "Akci se nepodařilo provést. Podívejte se na výstup a případně opakujte"
                    );
                }
            })
            .catch((error) => {
                console.error(error);
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };
    const actionPreview = commitResult ?? previewResponse;
    return (
        <>
            <h1>Náhled efektu akce {props.actionName}</h1>
            {!props.argsValid(debouncedArgs) ? (
                <div ref={messageRef}>
                    <ErrorMessage>Zadané argumenty jsou neplatné.</ErrorMessage>
                </div>
            ) : actionPreview ? (
                <div ref={messageRef}>
                    <ActionMessage response={actionPreview} />
                </div>
            ) : (
                <div
                    style={{
                        height:
                            loaderHeight > 0 ? loaderHeight + 48 : undefined,
                    }}
                >
                    <LoadingOrError
                        error={error}
                        message="Nemůžu načíst výsledek akce. Dejte o tom vědět Honzovi a Maarovi"
                    />
                </div>
            )}
            <div className="row">
                <Button
                    label="Zpět"
                    disabled={submitting}
                    onClick={props.onAbort}
                    className="my-4 mx-0 w-full bg-red-500 hover:bg-red-600 md:w-1/2"
                />
                <Button
                    label={submitting ? "Odesílám data" : "Zahájit akci"}
                    disabled={
                        submitting ||
                        !previewResponse?.success ||
                        !props.argsValid(debouncedArgs)
                    }
                    onClick={handleSubmit}
                    className="my-4 mx-0 w-full bg-green-500 hover:bg-green-600 md:w-1/2"
                />
            </div>
        </>
    );
}

export function ActionMessage(props: { response: ActionResponse }) {
    let Message = props.response.success
        ? props.response.expected
            ? SuccessMessage
            : WarningMessage
        : ErrorMessage;
    return (
        <Message>
            <CiviMarkdown>{props.response.message}</CiviMarkdown>
        </Message>
    );
}

function ActionPreviewPhase<TArgs>(props: {
    actionName: string | JSX.Element;
    actionId: string;
    actionArgs: TArgs;
    onAbort: () => void;
    changePhase: (phase: ActionPhase, data: ActionResponse) => void;
    argsValid: (args: TArgs) => boolean;
    ignoreGameStop?: boolean;
    ignoreCost?: boolean;
    ignoreThrows?: boolean;
}) {
    const { previewResponse, error, debouncedArgs } = useActionPreview({
        actionId: props.actionId,
        actionArgs: props.actionArgs,
        argsValid: props.argsValid,
        ignoreGameStop: props.ignoreGameStop,
        ignoreCost: props.ignoreCost,
        ignoreThrows: props.ignoreThrows,
    });
    const [lastArgs, setLastArgs] = useState<{
        actionId: string;
        args: TArgs;
        ignoreCost?: boolean;
        ignoreGameStop?: boolean;
    }>();
    const [submitting, setSubmitting] = useState(false);
    const [initiateResult, setInitiateResult] = useState<ActionResponse>();
    const [loaderHeight, setLoaderHeight] = useState(0);
    const [messageRef, { height }] = useElementSize();
    const { mutate } = useSWRConfig();
    const setActiveAction = useSetAtom(activeActionIdAtom);
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    const { actions } = useUnfinishedActions();

    if (actions && actions.length != 0) {
        return <Navigate to={`/actions/team/${actions[0].id}`} />;
    }

    if (height != 0 && height != loaderHeight) {
        setLoaderHeight(height);
    }

    const currentArgs = {
        actionId: props.actionId,
        args: props.actionArgs,
        ignoreCost: props.ignoreCost,
        ignoreGameStop: props.ignoreGameStop,
    };
    if (!_.isEqual(lastArgs, currentArgs)) {
        setLastArgs(currentArgs);
        setInitiateResult(undefined);
    }

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<ActionResponse>("/game/actions/team/initiate/", {
                action: props.actionId,
                args: props.actionArgs,
                ignore_cost: props.ignoreCost,
                ignore_game_stop: props.ignoreGameStop,
            })
            .then((data) => {
                setSubmitting(false);
                let result = data.data;
                setActiveAction(result?.action ?? RESET);
                if (result.success) {
                    if (result.committed) {
                        setFinishedAction(result?.action ?? RESET);
                        mutate("/game/actions/team/unfinished");
                        props.changePhase(ActionPhase.finish, result);
                    } else {
                        props.changePhase(ActionPhase.diceThrowPhase, result);
                    }
                } else {
                    setInitiateResult(result);
                    toast.error(
                        "Akci se nepodařilo zahájit. Podívejte se na výstup a případně opakujte"
                    );
                }
            })
            .catch((error) => {
                console.error(error);
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };
    const actionPreview = initiateResult ?? previewResponse;
    return (
        <>
            <h1>Náhled efektu akce {props.actionName}</h1>
            {!props.argsValid(debouncedArgs) ? (
                <div ref={messageRef}>
                    <ErrorMessage>Zadané argumenty jsou neplatné.</ErrorMessage>
                </div>
            ) : actionPreview ? (
                <div ref={messageRef}>
                    <ActionMessage response={actionPreview} />
                </div>
            ) : (
                <div
                    style={{
                        height:
                            loaderHeight > 0 ? loaderHeight + 48 : undefined,
                    }}
                >
                    <LoadingOrError
                        error={error}
                        message="Nemůžu načíst výsledek akce. Dejte o tom vědět Honzovi a Maarovi"
                    />
                </div>
            )}
            <div className="row">
                <Button
                    label="Zpět"
                    disabled={submitting}
                    onClick={props.onAbort}
                    className="my-4 mx-0 w-full bg-red-500 hover:bg-red-600 md:w-1/2"
                />
                <Button
                    label={submitting ? "Odesílám data" : "Zahájit akci"}
                    disabled={
                        submitting ||
                        !previewResponse?.success ||
                        !props.argsValid(debouncedArgs)
                    }
                    onClick={handleSubmit}
                    className="my-4 mx-0 w-full bg-green-500 hover:bg-green-600 md:w-1/2"
                />
            </div>
        </>
    );
}

export function IgnoreActionDicePhase(props: {
    actionNumber: number;
    actionName: string | JSX.Element;
    changePhase: (phase: ActionPhase, data: ActionResponse) => void;
}) {
    const { mutate } = useSWRConfig();
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    axiosService
        .post<ActionResponse>(
            `/game/actions/team/${props.actionNumber}/commit/`,
            {
                throws: 0,
                dots: 0,
                ignore_throws: true,
            }
        )
        .then((data) => {
            let result = data.data;
            setFinishedAction(data.data.action ?? RESET);
            mutate("/game/actions/team/unfinished");
            props.changePhase(ActionPhase.finish, result);
        })
        .catch((error) => {
            console.error(error);
            toast.error(`Nastala neočekávaná chyba: ${error}`);
        });

    return (
        <>
            <h1>Ignoruje se házení kostkou pro akci {props.actionName}</h1>
            <InlineSpinner />
        </>
    );
}

export function ActionDicePhase(props: {
    actionNumber: number;
    message: string;
    actionName: string | JSX.Element;
    changePhase: (phase: ActionPhase, data: ActionResponse) => void;
}) {
    const { data: action, error: actionErr } =
        useSWR<ActionDiceRequirementsResponse>(
            `/game/actions/team/${props.actionNumber}/commit`,
            fetcher
        );
    const [throwInfo, setThrowInfo] = useState({ throws: 0, dots: 0 });
    const [submitting, setSubmitting] = useState(false);
    const { mutate } = useSWRConfig();
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    let header = <h1>Házení kostkou pro akci {props.actionName}</h1>;

    if (!action) {
        return (
            <>
                {header}
                <LoadingOrError
                    error={actionErr}
                    message="Nemůžu načíst házení kostkou pro akci. Dejte o tom vědět Honzovi a Maarovi"
                />
            </>
        );
    }

    let handleSubmit = () => {
        if (
            throwInfo.dots < action.requiredDots &&
            !window.confirm("Opravdu tým nenaházel dostatek?")
        )
            return;
        if (
            throwInfo.dots == 0 &&
            !window.confirm("Opravdu tým naházel 0? Pokračovat?")
        )
            return;
        setSubmitting(true);
        axiosService
            .post<ActionResponse>(
                `/game/actions/team/${props.actionNumber}/commit/`,
                {
                    throws: throwInfo.throws,
                    dots: throwInfo.dots,
                }
            )
            .then((data) => {
                setSubmitting(false);
                let result = data.data;
                setFinishedAction(data.data.action ?? RESET);
                mutate("/game/actions/team/unfinished");
                props.changePhase(ActionPhase.finish, result);
            })
            .catch((error) => {
                console.error(error);
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };
    let handleCancel = () => {
        if (
            throwInfo.dots != 0 ||
            window.confirm("Opravdu akci zrušit? Nespletl jsi se jen?")
        ) {
            setSubmitting(true);
            axiosService
                .post<ActionResponse>(
                    `/game/actions/team/${props.actionNumber}/revert/`
                )
                .then((data) => {
                    setSubmitting(false);
                    setFinishedAction(props.actionNumber);
                    mutate("/game/actions/team/unfinished");
                    let result = data.data;
                    props.changePhase(ActionPhase.finish, result);
                })
                .catch((error) => {
                    console.error(error);
                    setSubmitting(false);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                });
        }
    };

    let handleUpdate = (dots: number, throws: number) => {
        setThrowInfo({
            throws: throws >= 0 ? throws : 0,
            dots: dots >= 0 ? dots : 0,
        });
    };

    return (
        <>
            {header}
            <NeutralMessage className="my-0">
                <CiviMarkdown>{props.message}</CiviMarkdown>
                Je třeba naházet {action.requiredDots}. Cena hodu je{" "}
                {action.throwCost} práce.
            </NeutralMessage>
            <DiceThrowForm
                teamId={action.team}
                dots={throwInfo.dots}
                throws={throwInfo.throws}
                throwCost={action.throwCost}
                update={handleUpdate}
                enabled={!submitting}
            />

            <div className="row md:flex">
                <Button
                    label="Zrušit akci"
                    className="my-1 mx-0 w-full bg-red-300 hover:bg-red-400 md:mx-3 md:w-1/2"
                    disabled={submitting}
                    onClick={handleCancel}
                />
                <Button
                    label={submitting ? "Odesílám, počkej" : "Odeslat"}
                    className="my-1 mx-0 w-full bg-green-500 py-8 hover:bg-green-600 md:mx-3  md:w-1/2 md:py-1"
                    disabled={submitting}
                    onClick={handleSubmit}
                />
            </div>
        </>
    );
}

function DiceThrowForm(props: {
    teamId: string;
    dots: number;
    throws: number;
    throwCost: number;
    update: (dots: number, throws: number) => void;
    enabled: boolean;
}) {
    const [otherInput, setOtherInput] = useState<number>();
    const [otherInputRef, setOtherInputFocus] = useFocus();
    const { teamWork } = useTeamWork(props.teamId);

    const handleThrow = (amount: number) => {
        props.update(props.dots + amount, props.throws + 1);
    };
    const handleArbitraryThrow = () => {
        if (!_.isNil(otherInput)) {
            handleThrow(otherInput);
            setOtherInput(undefined);
            setOtherInputFocus();
        }
    };

    const throwsLeft =
        !_.isNil(teamWork) && _.isFinite(Number(teamWork))
            ? Math.floor(Number(teamWork) / props.throwCost - props.throws)
            : "??";

    return (
        <div className="w-full">
            <div className="container mt-0 w-full md:mt-4">
                <div className="mx-0 my-1 w-full px-0 md:inline-block md:w-2/5">
                    <div className="my-1 inline-block w-full px-3 text-left align-middle md:w-1/4 md:text-right">
                        Teček:
                    </div>
                    <div className="field inline-block w-full px-0 align-middle md:w-3/4">
                        <SpinboxInput
                            disabled={!props.enabled}
                            className="numberinput w-full"
                            value={props.dots}
                            onChange={(value: number) => {
                                props.update(value, props.throws);
                            }}
                        />
                    </div>
                </div>
                <div className="mx-0 my-1 w-full px-0 md:inline-block md:w-2/5">
                    <div className="my-1 inline-block w-full px-3 text-left align-middle md:w-1/4 md:text-right">
                        Hodů:
                    </div>
                    <div className="field inline-block w-full px-0 align-middle md:w-3/4">
                        <SpinboxInput
                            disabled={!props.enabled}
                            className="numberinput w-full"
                            value={props.throws}
                            onChange={(value: number) => {
                                props.update(props.dots, value);
                            }}
                        />
                    </div>
                </div>
                <div className="mx-0 my-0 w-full px-3 py-1 text-center font-bold md:inline-block md:w-1/5">
                    Zbývá {throwsLeft} hodů (pouze odhad)
                </div>
            </div>

            <div className="my-1 flex w-full flex-wrap">
                <Button
                    label="0"
                    className="mx-1 my-3 w-full  bg-red-500 hover:bg-red-600 md:mx-4"
                    onClick={() => handleThrow(0)}
                    disabled={!props.enabled}
                />
                <div className="mx-0 grid w-full grid-cols-5 gap-2 px-0 md:mx-3">
                    {Array.from(Array(20).keys()).map((i) => {
                        return (
                            <Button
                                key={i + 1}
                                label={String(i + 1)}
                                onClick={() => handleThrow(i + 1)}
                                className="mx-1 px-0 text-center md:py-2"
                                disabled={!props.enabled}
                            />
                        );
                    })}
                </div>
            </div>
            <div className="field my-1 flex w-full flex-wrap">
                <input
                    type="number"
                    ref={otherInputRef}
                    className="numberinput mx-0 w-full text-right md:mx-3 md:flex-1"
                    value={otherInput ?? ""}
                    onChange={(e) => {
                        if (e.target.checkValidity()) {
                            setOtherInput(
                                e.target.value !== ""
                                    ? parseInt(e.target.value)
                                    : undefined
                            );
                        }
                    }}
                    onKeyDown={(event) => {
                        if (event.key === "Enter") {
                            handleArbitraryThrow();
                        }
                    }}
                    disabled={!props.enabled}
                />
                <Button
                    label="Hod"
                    className="my-2 mx-0 w-full bg-blue-500 hover:bg-blue-600 md:my-0 md:mx-3 md:w-60"
                    onClick={handleArbitraryThrow}
                    disabled={!props.enabled || _.isNil(otherInput)}
                />
            </div>
        </div>
    );
}

export function ActionFinishPhase(props: {
    response: ActionResponse;
    actionName: string | JSX.Element;
    onFinish: () => void;
}) {
    const [canQuit, setCanQuit] = useState(false);
    const setActiveAction = useSetAtom(activeActionIdAtom);

    useEffect(() => {
        setActiveAction(RESET);
        if (!props.response?.stickers || props.response.stickers.length == 0) {
            setCanQuit(true);
        }
    }, [props.response]);

    return (
        <>
            <h1>
                Akce {props.actionName}{" "}
                {props.response.success ? "dokončena" : "skončila s chybou"}
            </h1>
            <ActionMessage response={props.response} />

            {props.response?.stickers && props.response.stickers.length > 0 && (
                <PrintStickers
                    stickers={props.response.stickers}
                    onPrinted={() => setCanQuit(true)}
                />
            )}

            <Button
                label={
                    canQuit ? "Budiž" : "Ještě je třeba vytisknout samolepky"
                }
                disabled={!canQuit}
                className="mb-20 w-full"
                onClick={props.onFinish}
            />
        </>
    );
}
