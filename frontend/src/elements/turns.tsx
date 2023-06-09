import _ from "lodash";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Turn } from "../types";
import { fetcher } from "../utils/axios";
import { LoadingOrError } from ".";

interface ServerTurn {
    id: number;
    startedAt?: string;
    enabled: boolean;
    duration: number;
}

function translateTurn(turn: ServerTurn): Turn {
    const startedAt = turn.startedAt ? new Date(turn.startedAt) : undefined;
    return {
        id: turn.id,
        startedAt,
        shouldStartAt: startedAt,
        enabled: turn.enabled,
        duration: turn.duration,
    };
}

export function useTurns() {
    const { data, error, mutate } = useSWR<Turn[]>("game/turns", (url) =>
        fetcher<ServerTurn[]>(url).then((data) => {
            const turns = data.map(translateTurn);
            turns.forEach((turn, i) => {
                const prevTurn = i > 0 ? turns[i - 1] : undefined;
                turn.shouldStartAt ??=
                    prevTurn?.enabled && !_.isNil(prevTurn.shouldStartAt)
                        ? new Date(
                              prevTurn.shouldStartAt.getTime() +
                                  1000 * prevTurn.duration
                          )
                        : undefined;
            });
            return turns;
        })
    );
    return { turns: data, error, mutate };
}

export function useCurrentTurn() {
    const { data, error, mutate } = useSWR<ServerTurn | { id: -1 }>(
        "/game/turns/active",
        fetcher,
        {
            refreshInterval: 5000,
        }
    );
    const isTurn = function (
        turn: ServerTurn | { id: -1 }
    ): turn is ServerTurn {
        return turn.id >= 0;
    };

    if (!data) {
        return {
            error,
            mutate,
        };
    }
    if (!isTurn(data)) {
        return {
            info: {
                id: data.id,
            },
            error: "The game is not running",
            mutate,
        };
    }

    const start = data.startedAt ? new Date(data.startedAt) : null;
    return {
        info: {
            id: data.id,
            start,
            end: !_.isNil(start)
                ? new Date(start.getTime() + 1000 * data.duration)
                : null,
        },
        mutate,
        error,
    };
}

export function CurrentTurnCountdown(): JSX.Element {
    const { info, mutate: reload, error } = useCurrentTurn();
    const [elapsed, setElapsed] = useState(0);

    useEffect(() => {
        const int = setInterval(() => {
            setElapsed(elapsed + 1);
        }, 1000);
        return () => clearInterval(int);
    }, [elapsed, setElapsed]);

    if (!info) {
        return (
            <LoadingOrError
                error={error}
                message="Nepovedlo se načíst aktuální kolo"
            />
        );
    }
    if (info.id == -1 || _.isNil(info.end)) {
        return <>Hra je aktuálně pozastavena</>;
    }

    const now = new Date();
    let remainingSecs = (info.end.getTime() - now.getTime()) / 1000;
    if (remainingSecs <= 0) {
        reload();
        remainingSecs = 0;
    }
    const minutes = Math.floor(remainingSecs / 60);
    const secs = Math.floor(remainingSecs % 60);
    return (
        <>
            Kolo {info.id}, zbývá {String(minutes).padStart(2, "0")}:
            {String(secs).padStart(2, "0")}
        </>
    );
}

export function TurnCountdownSticker() {
    return (
        <div className="mb-4 rounded-b border-t-4 px-4 py-3 shadow-md">
            <div className="generationInfo">
                <CurrentTurnCountdown />
            </div>
        </div>
    );
}
