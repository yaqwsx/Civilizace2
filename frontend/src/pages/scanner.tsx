import onScan from "onscan.js"
import { useEffect } from "react";
import { useNavigate } from "react-router-dom"

function decodeKeyEvent(event: KeyboardEvent) {
    if (event.code === "Space")
        return " ";
    if (event.code.startsWith("Digit"))
        return event.code.charAt(event.code.length - 1);
    if (event.code === "Slash")
        return "-";
    return onScan.decodeKeyEvent(event);
}


export function ScannerDispatcher() {
    const navigate = useNavigate();

    const handleCodes = (code: string) => {
        console.log("Scanned " + code);
        const items = code.split(" ").map(x => x.trim());
        let args: string[] = [];
        let page = null;
        items.forEach(item => {
            if (item.startsWith("tym-")) {
                args.push(`team=${item}`);
                return;
            }
            if (item.startsWith("vyr-")) {
                args.push(`entity=${item}`);
                page = "vyrobas";
                return;
            }
            if (item.startsWith("tech-")) {
                args.push(`entity=${item}`);
                page = "techs";
                return;
            }
        });
        if (page) {
            console.log("Navigating to " + `${page}#${args.join("&")}`);
            navigate(page)
            window.location.hash = `#${args.join("&")}`;
        }
    };

    useEffect(() => {
        onScan.attachTo(document, {
            onScan: handleCodes,
            keyCodeMapper: decodeKeyEvent
        })
        return () => {
            onScan.detachFrom(document);
        }
    }, [])

    return null;
}
