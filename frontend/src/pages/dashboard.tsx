import { CiviMarkdown } from "../elements";

export function DashboardMenu() {
    return <p>Dashboard Menu</p>;
}

let c = `Tady bude tag: <<tec-a>> Nebo ne?`

export function Dashboard() {
    return (
        <>
            <p>Dashboard</p>
            <CiviMarkdown>
                {c}
            </CiviMarkdown>
        </>
    );
}
