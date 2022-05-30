import React, { useEffect, useState } from "react";
import {
    ActionCommitResponse,
    ActionResponse,
    ActionStatus,
    Team,
} from "../types";
import axiosService, { fetcher } from "../utils/axios";

import {
    Button,
    CiviMarkdown,
    ComponentError,
    LoadingOrError,
    useFocus,
} from ".";
import { ErrorMessage, SuccessMessage } from "./messages";
import { toast } from "react-toastify";

import _ from "lodash";
import { Action } from "history";
import useSWR from "swr";
import { useTeamWork } from "./entities";

function useActionPreview(actionId: string, actionArgs: any) {
    const [preview, setPreview] = useState<ActionResponse | null>(null);
    const [error, setError] = useState<any>(null);
    console.log(actionArgs);
    useEffect(() => {
        setError(null);
        setPreview(null);

        axiosService
            .post<any, any>("/game/actions/dry/", {
                action: actionId,
                args: actionArgs,
            })
            .then((data) => {
                setError(null);
                setPreview(data.data);
            })
            .catch((error) => {
                setPreview(null);
                setError(error);
            });
    }, [actionId, actionArgs]);
    return {
        preview: preview,
        error: error,
    };
}

enum ActionPhase {
    initiatePhase = 0,
    diceThrowPhase = 1,
    finish = 2,
}

export function PerformAction(props: {
    team?: Team;
    actionName: string;
    actionId: string;
    actionArgs: any;
    extraPreview?: any;
    onFinish: () => void;
    onBack: () => void;
}) {
    const [phase, setPhase] = useState<any>({
        phase: ActionPhase.initiatePhase,
        data: null,
    });

    let changePhase = (phase: ActionPhase, data: any) => {
        setPhase({
            phase: phase,
            data: data,
        });
    };

    console.log(phase);

    if (phase.phase == ActionPhase.initiatePhase) {
        return (
            <>
                {props.extraPreview ? props.extraPreview : null}
                <ActionPreviewPhase
                    actionName={props.actionName}
                    actionId={props.actionId}
                    actionArgs={props.actionArgs}
                    onAbort={props.onBack}
                    changePhase={changePhase}
                />
            </>
        );
    }
    if (phase.phase == ActionPhase.diceThrowPhase) {
        return (
            <ActionDicePhase
                team={props.team}
                actionId={phase.data.action}
                message={phase.data.message}
                actionName={props.actionName}
                changePhase={changePhase}
            />
        );
    }

    if (phase.phase == ActionPhase.finish) {
        return <ActionFinishPhase response={phase.data} actionName={props.actionName} onFinish={props.onFinish}/>;
    }

    return <ErrorMessage>Toto nemělo nastat. Není to nic vážného, ale až budeš mít chvíli, řekni o tom Honzovi</ErrorMessage>
}

function ActionMessage(props: { response: ActionResponse }) {
    let Message = props.response.success ? SuccessMessage : ErrorMessage;
    return (
        <Message>
            <CiviMarkdown>{props.response.message}</CiviMarkdown>
        </Message>
    );
}

function ActionPreviewPhase(props: {
    actionName: string;
    actionId: string;
    actionArgs: any;
    onAbort: () => void;
    changePhase: (phase: ActionPhase, data: any) => void;
}) {
    const { preview, error } = useActionPreview(
        props.actionId,
        props.actionArgs
    );
    const [lastArgs, setLastArgs] = useState<any>([null, null]);
    const [submitting, setSubmitting] = useState(false);
    const [initiateResult, setInitiateResult] = useState<ActionResponse | null>(
        null
    );

    if (!_.isEqual(lastArgs, [props.actionId, props.actionArgs])) {
        setLastArgs([props.actionId, props.actionArgs]);
        setInitiateResult(null);
    }

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<any, any>("/game/actions/initiate/", {
                action: props.actionId,
                args: props.actionArgs,
            })
            .then((data) => {
                setSubmitting(false);
                console.log(data);
                let result = data.data;
                if (result.success) {
                    if (result.committed) {
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
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };

    let header = <h1>Náhled efektu akce {props.actionName}</h1>;

    if (!preview) {
        return (
            <>
                {header}
                <LoadingOrError
                    loading={!preview && !error}
                    error={error}
                    message="Nemůžu načíst výsledek akce. Dejte o tom vědět Honzovi a Maarovi"
                />
            </>
        );
    }

    return (
        <>
            {header}
            <ActionMessage response={initiateResult || preview} />
            <div className="row">
                <Button
                    label="Zpět"
                    disabled={submitting}
                    onClick={props.onAbort}
                    className="my-4 mx-0 w-full bg-red-500 hover:bg-red-600 md:w-1/2"
                />
                <Button
                    label={submitting ? "Odesílám data" : "Zahájit akci"}
                    disabled={submitting || !preview.success}
                    onClick={handleSubmit}
                    className="my-4 mx-0 w-full bg-green-500 hover:bg-green-600 md:w-1/2"
                />
            </div>
        </>
    );
}

function ActionDicePhase(props: {
    team?: Team;
    actionId: Number;
    message: string;
    actionName: string;
    changePhase: (phase: ActionPhase, data: any) => void;
}) {
    const { data: action, error: actionErr } = useSWR<ActionCommitResponse>(
        `/game/actions/${props.actionId}/commit`,
        fetcher
    );
    const [throwInfo, setThrowInfo] = useState({ throws: 0, dots: 0 });
    const [submitting, setSubmitting] = useState(false);

    let handleSubmit = () => {
        if (
            throwInfo.dots != 0 ||
            window.confirm("Opravdu tým naházel 0? Pokračovat?")
        ) {
            setSubmitting(true);
            axiosService
                .post<any, any>(`/game/actions/${props.actionId}/commit/`, {
                    throws: throwInfo.throws,
                    dots: throwInfo.dots,
                })
                .then((data) => {
                    setSubmitting(false);
                    console.log(data);
                    let result = data.data;
                    props.changePhase(ActionPhase.finish, result);
                })
                .catch((error) => {
                    setSubmitting(false);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                });
        }
    };
    let handleCancel = () => {
        if (
            throwInfo.dots != 0 ||
            window.confirm("Opravdu akci zrušit? Nespletl jsi se jen?")
        ) {
            setSubmitting(true);
            axiosService
                .post<any, any>(`/game/actions/${props.actionId}/cancel/`)
                .then((data) => {
                    setSubmitting(false);
                    console.log(data);
                    let result = data.data;
                    props.changePhase(ActionPhase.finish, result);
                })
                .catch((error) => {
                    setSubmitting(false);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                });
        }
    };

    let handleUpdate = (dots: number, throws: number) =>
        setThrowInfo({
            throws: throws,
            dots: dots,
        });

    let header = <h1>Házení kostkou pro akci {props.actionName}</h1>;

    if (!action) {
        return (
            <>
                {header}
                <LoadingOrError
                    loading={!action && !actionErr}
                    error={actionErr}
                    message="Nemůžu načíst házení kostkou pro akci. Dejte o tom vědět Honzovi a Maarovi"
                />
            </>
        );
    }

    return (
        <>
            {header}
            <CiviMarkdown>{props.message}</CiviMarkdown>
            <DiceThrowForm
                team={props.team}
                dots={throwInfo.dots}
                throws={throwInfo.throws}
                update={handleUpdate}
                enabled={!submitting}
            />
            <Button
                label={submitting ? "Odesílám, počkej" : "Odeslat"}
                className="my-1 mx-0 w-full bg-green-500  hover:bg-green-600 md:mx-3"
                disabled={submitting}
                onClick={handleSubmit}
            />

            <Button
                label="Zrušit akci"
                className="my-1 mx-0 mt-5 w-full  bg-red-300 hover:bg-red-400 md:mx-3"
                disabled={submitting}
                onClick={handleCancel}
            />
        </>
    );
}

function DiceThrowForm(props: {
    team?: Team;
    dots: number;
    throws: number;
    update: (dots: number, throws: number) => void;
    enabled: boolean;
}) {
    const [otherInput, setOtherInput] = useState<number | string>("");
    const [otherInputRef, setOtherInputFocus] = useFocus();
    const { teamWork } = useTeamWork(props.team);
    useEffect(() => {
        setOtherInputFocus();
    });

    const handleThrow = (amount: number) => {
        props.update(props.dots + amount, props.throws + 1);
        setOtherInputFocus();
    };
    const handleArbitraryThrow = () => {
        // @ts-ignore
        if (!isNaN(otherInput))
            // @ts-ignore
            props.update(props.dots + otherInput, props.throws + 1);
        setOtherInput("");
    };
    const handleKeyDown = (event: any) => {
        if (event.key === "Enter") {
            handleArbitraryThrow();
        }
    };

    return (
        <div className="w-full">
            <div className="container mt-4 w-full">
                <div className="mx-0 my-1 w-full px-0 md:w-1/3">
                    <div className="inline-block w-1/3 px-3 text-right align-middle">
                        Teček:
                    </div>
                    <div className="field inline-block w-2/3 px-0 align-middle">
                        <input
                            type="number"
                            disabled={!props.enabled}
                            className="numberinput w-full"
                            value={props.dots}
                            onChange={(e: any) => {
                                props.update(
                                    parseInt(e.target.value),
                                    props.throws
                                );
                            }}
                        />
                    </div>
                </div>
                <div className="mx-0 my-1 w-full px-0 md:w-1/3">
                    <div className="inline-block w-1/3 px-3 text-right align-middle">
                        Hodů:
                    </div>
                    <div className="field inline-block w-2/3 px-0 align-middle">
                        <input
                            type="number"
                            disabled={!props.enabled}
                            className="numberinput w-full"
                            value={props.throws}
                            onChange={(e: any) => {
                                props.update(
                                    props.dots,
                                    parseInt(e.target.value)
                                );
                            }}
                        />
                    </div>
                </div>
                <div className="mx-0 my-1 w-full px-0 md:w-1/3">
                    <div className="inline-block w-1/3 px-3 text-right align-middle">
                        Práce:
                    </div>
                    <div className="field inline-block w-2/3 px-0 align-middle">
                        {props.throws * 5} /{" "}
                        {teamWork !== null ? teamWork : "??"} (pouze odhad)
                    </div>
                </div>
            </div>

            <div className="my-5 w-full">
                <Button
                    label="0"
                    className="mx-0 my-3 w-full  bg-red-500 hover:bg-red-600 md:mx-3"
                    onClick={() => handleThrow(0)}
                    disabled={!props.enabled}
                />
                <div className="mx-auto grid grid-cols-5 gap-4 px-0">
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
            <div className="field my-5 flex w-full flex-wrap">
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

function ActionFinishPhase(props: {
    response: ActionResponse;
    actionName: string;
    onFinish: () => void;
}) {
    return (
        <>
            <h1>Akce {props.actionName} dokončena</h1>
            <ActionMessage response={props.response} />
            <Button label="Budiž" className="w-full mb-20" onClick={props.onFinish} />
        </>
    );
}
