import _ from "lodash";
import { useState } from "react";
import { toast } from "react-toastify";
import { useSWRConfig } from "swr";
import { Button, classNames, LoadingOrError, SpinboxInput } from "../elements";
import { CurrentTurnCountdown, useTurns } from "../elements/turns";
import { Task, Turn } from "../types";
import axiosService from "../utils/axios";
import { useHideMenu } from "./atoms";

export function TurnsMenu() {
    return null;
}

export function Turns() {
    useHideMenu();
    const { mutate: globalMutate } = useSWRConfig();
    const { turns, error } = useTurns();

    let turnsMutate = () => {
        globalMutate("game/turns");
        globalMutate("game/turns/active");
    };

    if (!turns) {
        return <LoadingOrError error={error} message="Nastala chyba" />;
    }

    return (
        <>
            <h1>Správa kol</h1>

            <CurrentTurnCountdown />

            <div className="w-full p-0">
                {turns.map((t) => (
                    <TurnComp key={t.id} turn={t} turnsMutate={turnsMutate} />
                ))}
            </div>
        </>
    );
}

enum TurnState {
    ended,
    active,
    future,
    disabled,
}

function getTurnState(turn: Turn): TurnState {
    if (!turn.enabled) {
        return TurnState.disabled;
    }
    if (_.isNil(turn.startedAt)) {
        return TurnState.future;
    }
    const now = new Date();
    const endsAt = new Date(turn.startedAt.getTime() + 1000 * turn.duration);
    if (now < endsAt) {
        return TurnState.active;
    }
    return TurnState.ended;
}

function TurnComp(props: { turn: Turn; turnsMutate: () => void }) {
    const [durationMins, setDurationMins] = useState<number>(
        Math.floor(props.turn.duration / 60)
    );
    const [enabled, setEnabled] = useState(props.turn.enabled);
    const [dirty, setDirty] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    let changeDuration = (v: number) => {
        setDurationMins(v);
        setDirty(true);
    };
    let changeEnabled = (v: boolean) => {
        setEnabled(v);
        setDirty(true);
    };

    let submit = () => {
        setSubmitting(true);
        axiosService
            .put<Task>(`game/turns/${props.turn.id}/`, {
                duration: 60 * durationMins,
                enabled,
            })
            .then((data) => {
                setSubmitting(false);
                setDirty(false);
                props.turnsMutate();
            })
            .catch((error) => {
                console.error(error);
                setSubmitting(false);
                toast.error(`Došlo k neočekávané chybě: ${error}`);
            });
    };

    const getTurnBgColor = (turnState: TurnState) => {
        switch (turnState) {
            case TurnState.ended:
                return "bg-blue-300";
            case TurnState.active:
                return "bg-green-300";
            case TurnState.future:
                return "bg-white";
            case TurnState.disabled:
                return "bg-gray-300";
            default:
                const exhaustiveCheck: never = turnState;
                return "";
        }
    };

    const bgColor = getTurnBgColor(getTurnState({ ...props.turn, enabled }));
    const editable = _.isNil(props.turn.startedAt);
    console.assert(
        _.isNil(props.turn.startedAt) ||
            props.turn.startedAt === props.turn.shouldStartAt,
        props.turn
    );
    return (
        <div
            className={classNames(
                "row my-2 flex w-full flex-wrap items-center rounded px-0 py-3 align-middle shadow md:flex-nowrap",
                bgColor
            )}
        >
            <div className="w-1/4 border-r-2 border-r-black px-3 text-right align-middle text-lg md:w-1/12">
                {props.turn.id}
            </div>
            <div className="w-3/4 px-3 align-middle md:w-2/12">
                {props.turn.shouldStartAt
                    ? `Začátek: ${props.turn.shouldStartAt.toLocaleString(
                          "cs-CZ",
                          {
                              weekday: "long",
                              hour: "2-digit",
                              minute: "2-digit",
                          }
                      )}`
                    : "Nelze určit začátek kola"}
            </div>
            <div className="flex- w-full px-3 align-middle md:w-auto">
                Trvání{" "}
                {!editable ? (
                    durationMins
                ) : (
                    <div className="field inline-block">
                        <SpinboxInput
                            value={durationMins}
                            className="text-center"
                            onChange={changeDuration}
                        />
                    </div>
                )}{" "}
                minut
            </div>
            <div className="w-1/2 px-3 align-middle md:w-1/12">
                {editable ? (
                    <>
                        <input
                            type="checkbox"
                            name="enabled"
                            checked={enabled}
                            className="checkboxinput mx-auto block h-12 w-12 align-middle"
                            onChange={(e) => changeEnabled(e.target.checked)}
                        />
                    </>
                ) : null}
            </div>
            <div className="w-1/2 px-3 text-center align-middle md:w-2/12">
                {editable && dirty ? (
                    <Button
                        label={submitting ? "Ukládám..." : "Uložit změny"}
                        className="mx-auto"
                        disabled={submitting}
                        onClick={submit}
                    />
                ) : null}
            </div>
        </div>
    );
}
