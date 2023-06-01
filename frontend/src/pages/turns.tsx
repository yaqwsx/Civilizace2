import useSWR, { useSWRConfig } from "swr";
import {
    Button,
    classNames,
    ComponentError,
    FormRow,
    LoadingOrError,
    SpinboxInput,
} from "../elements";
import { Turn } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { format as dateFormat } from "date-fns";
import { ChangeEvent, useState } from "react";
import { date } from "yup/lib/locale";
import { toast } from "react-toastify";
import { CurrentTurnCountdown } from "../elements/turns";
import { useHideMenu } from "./atoms";

export function TurnsMenu() {
    return null;
}

export function Turns() {
    useHideMenu();
    const { mutate: globalMutate } = useSWRConfig();
    const { data: turns, error: turnsError } = useSWR<Turn[]>(
        "game/turns",
        (url) =>
            fetcher(url).then((data) => {
                return data.map((r: Turn, i: number) => {
                    r.startedAt = r.startedAt
                        ? new Date(r.startedAt)
                        : undefined;
                    r.prev = i == 0 ? undefined : data[i - 1];
                    r.next = i == data.length - 1 ? undefined : data[i + 1];

                    if (r.startedAt) {
                        r.shouldStartAt = r.startedAt;
                    } else if (r.prev?.shouldStartAt && r.prev?.enabled) {
                        r.shouldStartAt = new Date(
                            r.prev.shouldStartAt.getTime() +
                                1000 * r.prev.duration
                        );
                    }
                    return r;
                });
            })
    );

    let turnsMutate = () => {
        globalMutate("game/turns");
        globalMutate("game/turns/active");
    };

    if (!turns) {
        return <LoadingOrError error={turnsError} message="Nastala chyba" />;
    }

    return (
        <>
            <h1>Správa kol</h1>

            <CurrentTurnCountdown />

            <div className="w-full p-0">
                {turns.map((t: Turn) => (
                    <TurnComp key={t.id} turn={t} turnsMutate={turnsMutate} />
                ))}
            </div>
        </>
    );
}

function TurnComp(props: { turn: Turn; turnsMutate: any }) {
    const [duration, setDuration] = useState<number>(
        Math.floor(props.turn.duration / 60)
    );
    const [enabled, setEnabled] = useState<boolean>(props.turn.enabled);
    const [dirty, setDirty] = useState<boolean>(false);
    const [submitting, setSubmitting] = useState<boolean>(false);

    let turn = props.turn;
    let changeDuration = (v: number) => {
        setDuration(v);
        setDirty(true);
    };
    let changeEnabled = (v: boolean) => {
        setEnabled(v);
        setDirty(true);
    };

    let submit = () => {
        setSubmitting(true);
        axiosService
            .put(`game/turns/${turn.id}/`, {
                duration: 60 * duration,
                enabled: enabled,
            })
            .then((data: any) => {
                setSubmitting(false);
                setDirty(false);
                props.turnsMutate();
            })
            .catch((error) => {
                setSubmitting(false);
                toast.error(`Došlo k neočekávané chybě: ${error}`);
            });
    };

    let now = new Date();
    let endsAt =
        turn.startedAt && turn?.next?.shouldStartAt
            ? turn.next.shouldStartAt
            : undefined;

    let bg = !enabled ? "bg-gray-300" : "bg-white";
    if (turn.startedAt) bg = "bg-blue-300";
    if (turn.startedAt && endsAt && turn.startedAt < now && now < endsAt)
        bg = "bg-green-300";
    let editable = !turn.startedAt;
    return (
        <div
            className={classNames(
                "row my-2 flex w-full flex-wrap items-center rounded px-0 py-3 align-middle shadow md:flex-nowrap",
                bg
            )}
        >
            <div className="w-1/4 border-r-2 border-r-black px-3 text-right align-middle text-lg md:w-1/12">
                {turn.id}
            </div>
            <div className="w-3/4 px-3 align-middle md:w-2/12">
                {turn.shouldStartAt
                    ? `Začátek: ${turn.shouldStartAt.toLocaleString("cs-CZ", {
                          weekday: "long",
                          hour: "2-digit",
                          minute: "2-digit",
                      })}`
                    : "Nelze určit začátek kola"}
            </div>
            <div className="flex- w-full px-3 align-middle md:w-auto">
                Trvání{" "}
                {!editable ? (
                    duration
                ) : (
                    <div className="field inline-block">
                        <SpinboxInput
                            value={duration}
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
