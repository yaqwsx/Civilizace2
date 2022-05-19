import useSWR from "swr";
import { ComponentError, FormRow, LoadingOrError } from "../elements";
import { Round, RoundSentinel } from "../types";
import { fetcher } from "../utils/axios";
import { combineErrors } from "../utils/error";
import { format as dateFormat } from "date-fns";
import { ChangeEvent, useState } from "react";

export function RoundsMenu() {
    return null;
}

export function Rounds() {
    const {
        data: rounds,
        error: roundsError,
        mutate: roundsMutate,
    } = useSWR<Round[]>("game/round", (url) =>
        fetcher(url).then((data) => {
            return data.map((r: Round) => {
                r.start = new Date(r.start);
                return r;
            });
        })
    );
    const {
        data: sentinel,
        error: sentinelError,
        mutate: sentinelMutate,
    } = useSWR<RoundSentinel>("game/round/sentinel", fetcher);

    if (!rounds || !sentinel || roundsError || sentinelError) {
        return (
            <LoadingOrError
                loading={!rounds || !sentinel}
                error={combineErrors([roundsError, sentinelError])}
                message="Nastala chyba"
            />
        );
    }

    let now = new Date();
    let futureRounds = rounds.filter((r) => r.start > now);

    return (
        <>
            <h1>Správa kol</h1>
            <RoundSentinelComp
                sentinel={sentinel}
                sentinelMutate={sentinelMutate}
                availableRounds={futureRounds}
            />

            <h2>Přehled kol:</h2>
            <table
                className="w-full"
                style={{
                    borderCollapse: "separate",
                    borderSpacing: "0 0.5em",
                }}
            >
                {rounds.map((r) => (
                    <RoundComp
                        key={r.seq}
                        round={r}
                        roundsMutate={roundsMutate}
                        sentinel={sentinel}
                    />
                ))}
            </table>
        </>
    );
}

function RoundSentinelComp(props: {
    sentinel: RoundSentinel;
    availableRounds: Round[];
    sentinelMutate: (newValue: RoundSentinel) => void;
}) {
    let handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
        let value = parseInt(e.target.value);
        // TBA submit
        props.sentinelMutate({
            seq: value,
        });
    };

    return (
        <>
            <h2>Zastavit po kole:</h2>
            <select
                className="select"
                onChange={handleChange}
                value={props.sentinel.seq}
            >
                {props.availableRounds.map((r) => (
                    <option key={r.seq} value={r.seq}>
                        Kolo {r.seq}, začíná {dateFormat(r.start, "d. M. H:mm")}
                    </option>
                ))}
            </select>
        </>
    );
}

function RoundComp(props: {
    round: Round;
    roundsMutate: () => void;
    sentinel: RoundSentinel;
}) {
    const [value, setValue] = useState<number | null>(null);
    const [changed, setChanged] = useState< boolean >(false);

    let bg = "bg-white";
    let minutes = Math.floor(props.round.length / 60);
    return (
        <tr className="my-2 p-2">
            <td className={`rounded-l-lg p-2 pr-4 text-right ${bg} shadow`}>
                {props.round.seq}
            </td>
            <td className={`p-2 ${bg} shadow`}>
                {dateFormat(props.round.start, "d. M. H:mm")}
            </td>
            <td className={`p-2 ${bg} field align-middle shadow`}>
                <p>
                    Trvání{" "}
                    {!props.round.editable ? (
                        minutes
                    ) : (
                        <input
                            className="mx-2 inline-block w-12 px-2 text-center align-middle"
                            value={minutes}
                        />
                    )}
                    {" "}minut
                </p>
            </td>
            <td className={`p-2 ${bg} rounded-r-lg shadow`}></td>
        </tr>
    );
}
