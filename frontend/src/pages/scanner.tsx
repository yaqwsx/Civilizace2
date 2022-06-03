import onScan from "onscan.js";
import { createContext, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function decodeKeyEvent(event: KeyboardEvent) {
    if (event.code === "Space") return " ";
    if (event.code.startsWith("Digit"))
        return event.code.charAt(event.code.length - 1);
    if (event.code === "Slash") return "-";
    return onScan.decodeKeyEvent(event);
}

interface ScannerContextType {
    subscribe: (callback: (content: string[]) => void) => void;
    unsubscribe: (callback: (content: string[]) => void) => void;
}

export const ScannerContext = createContext<ScannerContextType>({
    subscribe: () => {},
    unsubscribe: () => {},
});

export function ScannerDispatcher(props: { children: any }) {
    const [consumers, setConsumers] = useState<((content: string[]) => void)[]>(
        []
    );
    const handleCodes = (code: string) => {
        console.log("Scanned " + code, consumers);
        const items = code.split(" ").map((x) => x.trim());
        consumers.forEach((c) => {
            c(items);
        });
    };

    let subscribe = useCallback((f: (content: string[]) => void) => {
        console.log("Subscribed!", f, consumers.concat([f]));
        setConsumers(consumers.concat([f]));
    }, []);
    let unsubscribe = useCallback((f: (content: string[]) => void) => {
        console.log("Unsubscribed!", f);
        setConsumers(consumers.filter((x) => x != f));
    }, []);

    useEffect(() => {
        onScan.attachTo(document, {
            onScan: handleCodes,
            keyCodeMapper: decodeKeyEvent,
        });
        return () => {
            onScan.detachFrom(document);
        };
    }, []);

    return (
        <ScannerContext.Provider
            value={{
                subscribe: subscribe,
                unsubscribe: unsubscribe,
            }}
        >
            {props.children}
        </ScannerContext.Provider>
    );
}
