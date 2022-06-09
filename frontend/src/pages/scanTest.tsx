import { useState } from "react";
import { useScanner } from "./scanner";

export function ScanTest() {
    const [codes, setCodes] = useState<string[][]>([]);
    useScanner((c) => {
        let newCodes = codes;
        newCodes.push(c);
        setCodes(newCodes);
    });

    return <>
        <h1>Testování čtečky:</h1>
        {
            codes.map((v, i) => {
                return <div key={i} className="w-full font-mono my-2">
                    {JSON.stringify(v)}
                </div>
            })
        }
    </>
}
