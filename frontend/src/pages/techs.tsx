import classNames from "classnames";
import { useState } from "react";
import useSWR from "swr";
import { FormRow, InlineSpinner, ComponentError, LoadingOrError, Row, Button } from "../elements";
import { useTeamTechs } from "../elements/entities";
import {
    useTeamFromUrl,
    TeamSelector,
    TeamRowIndicator,
} from "../elements/team";
import { Team, TeamEntityTech } from "../types";

export function TechMenu() {
    return null;
}

export function Tech() {
    const { team, setTeam, loading, error } = useTeamFromUrl();

    if (loading || error)
        return <LoadingOrError loading={loading} error={error} message={"Nemůžu načíst týmy"}/>


    const handleTeamChange = (t: Team) => {
        setTeam(t);
    };

    return (
        <>
            <h2 className="text-lg">
                Spravovat výzkum
                {team ? ` pro tým ${team.name}` : null}
            </h2>
            <FormRow label="Vyber tým:">
                <TeamSelector onChange={handleTeamChange} active={team} />
            </FormRow>
            <TeamRowIndicator team={team} />
            {
                team ? <TechListing team={team}/> : null
            }
        </>
    );
}

function sortTechs(techs: TeamEntityTech[]) {
    return techs;
}

function TechListing(props: { team: Team }) {
    const { techs, loading, error } = useTeamTechs(props.team);

    if (loading || error || !techs)
        return <LoadingOrError loading={loading} error={error} message={"Nemůžu načíst technologie pro tým."}/>


    const researchingTechs = Object.values(techs)
        .filter((t) => t.status === "researching");
    const availableTechs = Object.values(techs)
        .filter((t) => t.status === "available");
    const ownedTechs = Object.values(techs)
        .filter((t) => t.status === "owned");

    console.log(techs);
    console.log(researchingTechs)

    return (<>
        <h2 className="text-xl">{props.team.name} aktuálně zkoumají:</h2>
        {
            researchingTechs ? <TechList team={props.team} techs={researchingTechs}/>
                             : <p>Tým {props.team.name} nic nezkoumá.</p>
        }
        <h2 className="text-xl">{props.team.name} mohou začít zkoumat:</h2>
        {
            availableTechs ? <TechList team={props.team} techs={availableTechs}/>
                             : <p>Tým {props.team.name} nemůže nic zkoumat. Ten je ale drný nebo je to bug</p>
        }
        <h2 className="text-xl">{props.team.name} mají vyzkoumáno:</h2>
        {
            ownedTechs ? <TechList team={props.team} techs={ownedTechs}/>
                             : <p>Tým {props.team.name} nevlastní žádné technologie. Což je asi bug.</p>
        }
    </>)
}

function TechList(props: {
    team: Team;
    techs: TeamEntityTech[];
}) {
    return (<div className="pl-4">
        {
            props.techs.map(t => <TechItem team={props.team} tech={t}/>)
        }
    </div>);
}

function TechItem(props: {
    team: Team;
    tech: TeamEntityTech;
}) {
    const [expanded, setExpanded] = useState<boolean>(false);
    let tech = props.tech;

    return (<div className="w-full my-2 flex flex-wrap rounded bg-gray-300 py-2 px-4">
        <div className="w-full md:w-1/3 align-middle my-2">
            <span className="text-xl mr-3 align-middle">{tech.name}</span>
            <span className="text-sm text-gray-600 align-middle">({tech.id})</span>
            {
                tech.assignedTask
                    ? <span className="ml-8 text-sm text-gray-600 align-middle">zadáno mají: {tech.assignedTask.name}</span>
                    : null
            }
        </div>
        <div className="w-full md:w-2/3 flex">
            {
                tech.status === "researching" ? <>
                    <Button label="Zobrazit úkol" className="bg-blue-500 hover:bg-blue-600 ml-0"/>
                    <Button label="Dokončit zkoumání" className="bg-green-500 hover:bg-green-600"/>
                    <Button label="Změnit úkol" className="bg-orange-500 hover:bg-orange-600 mr-0"/>
                    </> : null
            }
            {
                tech.status === "available" ? <>
                    <Button label="Začít zkoumat" className="bg-green-500 hover:bg-green-600 ml-0"/>
                </> : null
            }
        </div>
    </div>);
}
