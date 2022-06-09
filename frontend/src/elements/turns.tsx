import { useEffect, useState } from "react";
import useSWR from "swr";
import { fetcher } from "../utils/axios";

export function useCurrentTurn() {
    const { data, error, mutate } = useSWR<any>("/game/turns/active", fetcher, {
        refreshInterval: 5000,
    });

    if (data) {
        return {
            info: {
                id: data.id,
                start: data.startedAt ? new Date(data.startedAt) : null,
                end: data.startedAt
                    ? new Date(
                          new Date(data.startedAt).getTime() +
                              1000 * data.duration
                      )
                    : null,
            },
            reload: mutate,
            error: error,
        };
    }
    return {
        error: error,
        mutate: mutate,
    };
}

export function CurrentTurnCountdown() {
    const { info, reload, error } = useCurrentTurn();
    const [elapsed, setElapsed] = useState<number>(0);

    useEffect(() => {
        let int = setInterval(() => {
            setElapsed(elapsed + 1);
        }, 1000);
        return () => clearInterval(int);
    }, [elapsed, setElapsed]);

    let now = new Date();

    if (!error && !info) return "Načítám";
    if (error) return error.toString();
    if (info?.id == -1 || !info?.end) return "Hra je aktuálně pozastavena";

    let remainingSecs = (info.end.getTime() - now.getTime()) / 1000;
    if (remainingSecs <= 0) {
        reload();
        remainingSecs = 0;
    }
    let minutes = Math.floor(remainingSecs / 60);
    let secs = Math.floor(remainingSecs % 60);
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
                <CurrentTurnCountdown/>
            </div>
        </div>
    );
}
