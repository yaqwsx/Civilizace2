import { useEffect, useState } from "react";
import { Dialog, LoadingOrError } from "../elements";
import { useCurrentTurn } from "../elements/turns";

export function InfoScreen() {
    return (
        <>
            <div className="flex min-h-screen flex-col bg-gray-100 font-sans leading-normal tracking-normal">
                <div className="mx-auto w-full flex-grow pt-1">
                    <div className="mb-16 w-full px-2 py-10 leading-normal text-gray-800 md:mt-2 md:px-0">
                        <InfoScreenContent />
                    </div>
                </div>

                <footer className="border-t border-gray-400 bg-white shadow">
                    <div className="container mx-auto flex max-w-md py-8"></div>
                </footer>
            </div>
        </>
    );
}

function InfoScreenContent() {
    return (
        <div className="text-center">
            <Countdown />
            <PublicAnnouncements />
            <AutoFeedDialog />
        </div>
    );
}

function Countdown() {
    const { info, reload, error } = useCurrentTurn();
    const [elapsed, setElapsed] = useState<number>(0);

    useEffect(() => {
        let int = setInterval(() => {
            setElapsed(elapsed + 1);
        }, 1000);
        return () => clearInterval(int);
    }, [elapsed, setElapsed]);

    let now = new Date();

    if (!error && !info) {
        return (
            <LoadingOrError
                loading={!error && !info}
                error={error}
                message="Něco se nepovedlo"
            />
        );
    }

    let paused = info?.id == -1 || !info?.end;

    let minutes = 0;
    let secs = 0;
    if (!paused) {
        // @ts-ignore
        let remainingSecs = (info.end.getTime() - now.getTime()) / 1000;
        if (remainingSecs <= 0) {
            // @ts-ignore
            reload();
            remainingSecs = 0;
        }
        minutes = Math.floor(remainingSecs / 60);
        secs = Math.floor(remainingSecs % 60);
    }

    return (
        <>
            <h1 style={{ fontSize: "80px" }} className="mb-12 p-5">
                {paused
                    ? "Hra je aktuálně pozastavena"
                    : // @ts-ignore
                      `Probíhá ${info.id}. kolo`}
            </h1>
            <div style={{ fontSize: "300px" }} className="leading-none">
                {!paused &&
                    `${String(minutes).padStart(2, "0")}:${String(
                        secs
                    ).padStart(2, "0")}`}
            </div>
        </>
    );
}

function PublicAnnouncements() {
    return (
        <div className="container mx-auto">
            <h1>Poslední veřejná oznámení:</h1>
            <div id="announcements" className="text-left"></div>
        </div>
    );
}

function AutoFeedDialog() {
    return null;
}
