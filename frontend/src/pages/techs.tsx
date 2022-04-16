import classNames from "classnames";
import useSWR from "swr";
import { FormRow, InlineSpinner, ComponentError, LoadingOrError } from "../elements";
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
        <h2 className="text-lg">Aktuálně zkoumají:</h2>
        {
            researchingTechs ? <TechList team={props.team} techs={researchingTechs}/>
                             : <p>Tým {props.team.name} nic nezkoumá.</p>
        }
        <h2 className="text-lg">Mohou začít zkoumat:</h2>
        {
            availableTechs ? <TechList team={props.team} techs={availableTechs}/>
                             : <p>Tým {props.team.name} nemůže nic zkoumat. Ten je ale drný nebo je to bug</p>
        }
        <h2 className="text-lg">Už mají hotovo:</h2>
        {
            ownedTechs ? <TechList team={props.team} techs={ownedTechs}/>
                             : <p>Tým {props.team.name} nevlastní žádné technologie. Což je asi bug.</p>
        }
    </>)


    return null;
}

function TechList(props: {
    team: Team,
    techs: TeamEntityTech[],
}) {
    console.log(props.techs);
    return (<>{
        props.techs.map(t => {
            return <p>{t.id}</p>
        })
    }</>)
}
