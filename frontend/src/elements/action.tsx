import { useEffect, useState } from "react";
import {
    ActionCommitResponse,
    ActionResponse,
    UnfinishedAction,
} from "../types";
import axiosService, { fetcher } from "../utils/axios";

import { toast } from "react-toastify";
import {
    Button,
    CiviMarkdown,
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
        {
            refreshInterval: refreshInterval,
        }
    );
    const [activeAction] = useAtom(activeActionIdAtom);
    const [finishedAction] = useAtom(finishedActionIdAtom);
    return {
        actions: actions
            ? actions.filter(
                  (a: UnfinishedAction) =>
                      a.id != activeAction && a.id != finishedAction
              )
            : undefined,
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

export function useActionPreview(props: {
    actionId: string;
    actionArgs: any;
    argsValid: (args: any) => boolean;
    ignoreGameStop?: boolean;
    ignoreCost?: boolean;
    ignoreThrows?: boolean;
    isNoInit?: boolean;
}) {
    const [preview, setPreview] = useState<ActionResponse | null>(null);
    const [error, setError] = useState<any>(null);

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
        setError(null);
        setPreview(null);

        if (
            !props.actionArgs ||
            !debounced.args ||
            !props.argsValid(debounced.args)
        )
            return;

        axiosService
            .post<any, any>(
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
                setTimeout(() => {
                    setError(null);
                    setPreview(data.data);
                }, 0);
            })
            .catch((error) => {
                setPreview(null);
                setError(error);
            });
    }, [props.actionId, debounced]);

    return {
        preview: preview,
        error: error,
        debouncedArgs: debounced.args,
    };
}

export enum ActionPhase {
    initiatePhase = 0,
    diceThrowPhase = 1,
    finish = 2,
}

export function PerformAction(props: {
    actionName: any;
    actionId: string;
    actionArgs: any;
    argsValid?: (args: any) => boolean;
    extraPreview?: any;
    onFinish: () => void;
    onBack: () => void;
    ignoreCost?: boolean;
    ignoreGameStop?: boolean;
    ignoreThrows?: boolean;
}) {
    const [phase, setPhase] = useState<{ phase: ActionPhase; data?: any }>({
        phase: ActionPhase.initiatePhase,
    });
    const setActiveAction = useSetAtom(activeActionIdAtom);

    useEffect(() => {
        return () => {
            setActiveAction(RESET);
        };
    }, []);

    let argsValid = props.argsValid ?? (() => true);

    let changePhase = (phase: ActionPhase, data: any) => {
        setPhase({
            phase: phase,
            data: data,
        });
    };

    if (phase.phase == ActionPhase.initiatePhase) {
        return (
            <>
                {props.extraPreview ?? null}
                <ActionPreviewPhase
                    actionName={props.actionName}
                    actionId={props.actionId}
                    actionArgs={props.actionArgs}
                    onAbort={props.onBack}
                    changePhase={changePhase}
                    argsValid={argsValid}
                    ignoreGameStop={props.ignoreGameStop}
                    ignoreCost={props.ignoreCost}
                    ignoreThrows={props.ignoreThrows}
                />
                <div className="my-8 h-1 w-full" />
            </>
        );
    }
    if (phase.phase == ActionPhase.diceThrowPhase) {
        if (props.ignoreThrows) {
            return (
                <>
                    <IgnoreActionDicePhase
                        actionNumber={phase.data.action}
                        message={phase.data.message}
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

    return (
        <ErrorMessage>
            Toto nemělo nastat. Není to nic vážného, ale až budeš mít chvíli,
            řekni o tom Honzovi
        </ErrorMessage>
    );
}

export function PerformNoInitAction(props: {
    actionName: any;
    actionId: string;
    actionArgs: any;
    argsValid?: (args: any) => boolean;
    extraPreview?: any;
    onFinish: () => void;
    onBack: () => void;
    ignoreGameStop?: boolean;
}) {
    const [completedData, setCompletedData] = useState<any>(undefined);
    const setActiveAction = useSetAtom(activeActionIdAtom);

    useEffect(() => {
        return () => {
            setActiveAction(RESET);
        };
    }, []);

    let argsValid =
        props.argsValid === undefined ? () => true : props.argsValid;

    if (completedData === undefined) {
        return (
            <>
                {props.extraPreview ? props.extraPreview : undefined}
                <NoInitActionPreviewPhase
                    actionName={props.actionName}
                    actionId={props.actionId}
                    actionArgs={props.actionArgs}
                    onAbort={props.onBack}
                    changePhase={(_, data) =>
                        setCompletedData(data === undefined ? {} : data)
                    }
                    argsValid={argsValid}
                    ignoreGameStop={props.ignoreGameStop}
                />
                <div className="my-8 h-1 w-full" />
            </>
        );
    }

    if (completedData !== undefined) {
        return (
            <>
                <ActionFinishPhase
                    response={completedData}
                    actionName={props.actionName}
                    onFinish={props.onFinish}
                />
                <div className="my-8 h-1 w-full" />
            </>
        );
    }

    return (
        <ErrorMessage>
            Toto nemělo nastat. Není to nic vážného, ale až budeš mít chvíli,
            řekni o tom Honzovi
        </ErrorMessage>
    );
}

function NoInitActionPreviewPhase(props: {
    actionName: any;
    actionId: string;
    actionArgs: any;
    onAbort: () => void;
    changePhase: (phase: ActionPhase, data: any) => void;
    argsValid: (args: any) => boolean;
    ignoreGameStop?: boolean;
}) {
    const { preview, error, debouncedArgs } = useActionPreview({
        actionId: props.actionId,
        actionArgs: props.actionArgs,
        argsValid: props.argsValid,
        ignoreGameStop: props.ignoreGameStop,
        isNoInit: true,
    });
    const [lastArgs, setLastArgs] = useState<[string, any] | undefined>(
        undefined
    );
    const [submitting, setSubmitting] = useState(false);
    const [commitResult, setCommitResult] = useState<
        ActionResponse | undefined
    >(undefined);
    const [loaderHeight, setLoaderHeight] = useState(0);
    const [messageRef, { height }] = useElementSize();
    const setActiveAction = useSetAtom(activeActionIdAtom);
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    if (height != 0 && height != loaderHeight) setLoaderHeight(height);

    if (!_.isEqual(lastArgs, [props.actionId, props.actionArgs])) {
        setLastArgs([props.actionId, props.actionArgs]);
        setCommitResult(undefined);
    }

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<any, any>("/game/actions/noinit/commit/", {
                action: props.actionId,
                args: props.actionArgs,
                ignore_game_stop: props.ignoreGameStop,
            })
            .then((data) => {
                setSubmitting(false);
                let result = data.data;
                setActiveAction(result?.action ?? RESET);
                if (result.success) {
                    props.changePhase(ActionPhase.finish, result);
                    setFinishedAction(result?.action ?? RESET);
                } else {
                    setCommitResult(result);
                    toast.error(
                        "Akci se nepodařilo provést. Podívejte se na výstup a případně opakujte"
                    );
                }
            })
            .catch((error) => {
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };
    const actionPreview = commitResult ?? preview;
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
                        !preview?.success ||
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

function ActionPreviewPhase(props: {
    actionName: any;
    actionId: string;
    actionArgs: any;
    onAbort: () => void;
    changePhase: (phase: ActionPhase, data: any) => void;
    argsValid: (args: any) => boolean;
    ignoreGameStop?: boolean;
    ignoreCost?: boolean;
    ignoreThrows?: boolean;
}) {
    const { preview, error, debouncedArgs } = useActionPreview({
        actionId: props.actionId,
        actionArgs: props.actionArgs,
        argsValid: props.argsValid,
        ignoreGameStop: props.ignoreGameStop,
        ignoreCost: props.ignoreCost,
        ignoreThrows: props.ignoreThrows,
    });
    const [lastArgs, setLastArgs] = useState<
        | {
              actionId: string;
              args: any;
              ignoreCost?: boolean;
              ignoreGameStop?: boolean;
          }
        | undefined
    >(undefined);
    const [submitting, setSubmitting] = useState(false);
    const [initiateResult, setInitiateResult] = useState<
        ActionResponse | undefined
    >(undefined);
    const [loaderHeight, setLoaderHeight] = useState(0);
    const [messageRef, { height }] = useElementSize();
    const setActiveAction = useSetAtom(activeActionIdAtom);
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    const { actions } = useUnfinishedActions();

    if (actions && actions.length != 0) {
        return <Navigate to={`/actions/team/${actions[0].id}`} />;
    }

    if (height != 0 && height != loaderHeight) setLoaderHeight(height);

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
            .post<any, any>("/game/actions/team/initiate/", {
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
                        props.changePhase(ActionPhase.finish, result);
                        setFinishedAction(result?.action ?? RESET);
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
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };
    const actionPreview = initiateResult ?? preview;
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
                        !preview?.success ||
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
    message: string;
    actionName: any;
    changePhase: (phase: ActionPhase, data: any) => void;
}) {
    const { data: action, error: actionErr } = useSWR<ActionCommitResponse>(
        `/game/actions/team/${props.actionNumber}/commit`,
        fetcher
    );
    const { mutate } = useSWRConfig();

    const header = <h1>Házení kostkou pro akci {props.actionName}</h1>;

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

    axiosService
        .post<any, any>(`/game/actions/team/${props.actionNumber}/commit/`, {
            throws: 0,
            dots: 0,
            ignore_throws: true,
        })
        .then((data) => {
            let result = data.data;
            mutate("/game/actions/team/unfinished");
            props.changePhase(ActionPhase.finish, result);
        })
        .catch((error) => {
            toast.error(`Nastala neočekávaná chyba: ${error}`);
        });

    return (
        <>
            {header}
            <NeutralMessage className="my-0">
                Ignoruje se házení kostkou...
            </NeutralMessage>
        </>
    );
}

export function ActionDicePhase(props: {
    actionNumber: number;
    message: string;
    actionName: any;
    changePhase: (phase: ActionPhase, data: any) => void;
}) {
    const { data: action, error: actionErr } = useSWR<ActionCommitResponse>(
        `/game/actions/team/${props.actionNumber}/commit`,
        fetcher
    );
    const [throwInfo, setThrowInfo] = useState({ throws: 0, dots: 0 });
    const [submitting, setSubmitting] = useState(false);
    const { mutate } = useSWRConfig();
    const setActiveAction = useSetAtom(activeActionIdAtom);
    const setFinishedAction = useSetAtom(finishedActionIdAtom);

    useEffect(() => {
        return () => {
            setActiveAction(RESET);
        };
    }, [props.actionNumber]);

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
            .post<any, any>(
                `/game/actions/team/${props.actionNumber}/commit/`,
                {
                    throws: throwInfo.throws,
                    dots: throwInfo.dots,
                }
            )
            .then((data) => {
                setSubmitting(false);
                let result = data.data;
                setFinishedAction(props.actionNumber);
                mutate("/game/actions/team/unfinished");
                props.changePhase(ActionPhase.finish, result);
            })
            .catch((error) => {
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
                .post<any, any>(
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
                    setSubmitting(false);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                });
        }
    };

    let handleUpdate = (dots: number, throws: number) => {
        if (dots < 0) dots = 0;
        if (throws < 0) throws = 0;
        setThrowInfo({
            throws: throws,
            dots: dots,
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
    const [otherInput, setOtherInput] = useState<number | string>("");
    const [otherInputRef, setOtherInputFocus] = useFocus();
    const { teamWork } = useTeamWork(props.teamId);

    const handleThrow = (amount: number) => {
        props.update(props.dots + amount, props.throws + 1);
    };
    const handleArbitraryThrow = () => {
        // @ts-ignore
        if (!isNaN(otherInput))
            // @ts-ignore
            props.update(props.dots + otherInput, props.throws + 1);
        setOtherInput("");
        setOtherInputFocus();
    };
    const handleKeyDown = (event: any) => {
        if (event.key === "Enter") {
            handleArbitraryThrow();
        }
    };

    let throwsLeft =
        !_.isNil(teamWork) && _.isFinite(Number(teamWork))
            ? Math.floor(
                  (Number(teamWork) - props.throws * props.throwCost) /
                      props.throwCost
              )
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
                                key={i}
                                label={`${i + 1}`}
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
                    value={otherInput}
                    onChange={(e) => setOtherInput(parseInt(e.target.value))}
                    onKeyDown={handleKeyDown}
                    disabled={!props.enabled}
                />
                <Button
                    label="Hod"
                    className="my-2 mx-0 w-full bg-blue-500 hover:bg-blue-600 md:my-0 md:mx-3 md:w-60"
                    onClick={handleArbitraryThrow}
                    disabled={!props.enabled}
                />
            </div>
        </div>
    );
}

export function ActionFinishPhase(props: {
    response: ActionResponse;
    actionName: any;
    onFinish: () => void;
}) {
    const [canQuit, setCanQuit] = useState(false);

    useEffect(() => {
        if (!props.response?.stickers || props.response.stickers.length == 0)
            setCanQuit(true);
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
