import classNames from "classnames";
import { useState } from "react";
import useSWR from "swr";
import {
    FormRow,
    InlineSpinner,
    ComponentError,
    LoadingOrError,
    Row,
    Button,
    CiviMarkdown,
    Dialog,
} from "../elements";
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
        return (
            <LoadingOrError
                loading={loading}
                error={error}
                message={"Nemůžu načíst týmy"}
            />
        );

    const handleTeamChange = (t: Team) => {
        setTeam(t);
    };

    return (
        <>
            <h2>
                Spravovat výzkum
                {team ? ` pro tým ${team.name}` : null}
            </h2>
            <FormRow label="Vyber tým:">
                <TeamSelector onChange={handleTeamChange} active={team} />
            </FormRow>
            <TeamRowIndicator team={team} />
            {team ? <TechListing team={team} /> : null}
        </>
    );
}

function sortTechs(techs: TeamEntityTech[]) {
    return techs;
}

function TechListing(props: { team: Team }) {
    const { techs, loading, error } = useTeamTechs(props.team);

    if (loading || error || !techs)
        return (
            <LoadingOrError
                loading={loading}
                error={error}
                message={"Nemůžu načíst technologie pro tým."}
            />
        );

    const researchingTechs = sortTechs(
        Object.values(techs).filter((t) => t.status === "researching")
    );
    const availableTechs = sortTechs(
        Object.values(techs).filter((t) => t.status === "available")
    );
    const ownedTechs = sortTechs(
        Object.values(techs).filter((t) => t.status === "owned")
    );

    console.log(techs);
    console.log(researchingTechs);

    return (
        <>
            <h2>
                {props.team.name} aktuálně zkoumají:
            </h2>
            {researchingTechs ? (
                <TechList team={props.team} techs={researchingTechs} />
            ) : (
                <p>Tým {props.team.name} nic nezkoumá.</p>
            )}
            <h2>
                {props.team.name} mohou začít zkoumat:
            </h2>
            {availableTechs ? (
                <TechList team={props.team} techs={availableTechs} />
            ) : (
                <p>
                    Tým {props.team.name} nemůže nic zkoumat. Ten je ale drný
                    nebo je to bug
                </p>
            )}
            <h2>
                {props.team.name} mají vyzkoumáno:
            </h2>
            {ownedTechs ? (
                <TechList team={props.team} techs={ownedTechs} />
            ) : (
                <p>
                    Tým {props.team.name} nevlastní žádné technologie. Což je
                    asi bug.
                </p>
            )}
        </>
    );
}

function TechList(props: { team: Team; techs: TeamEntityTech[] }) {
    return (
        <div className="pl-4">
            {props.techs.map((t) => (
                <TechItem key={t.id} team={props.team} tech={t} />
            ))}
        </div>
    );
}

function TechItem(props: { team: Team; tech: TeamEntityTech }) {
    const [taskShown, setTaskShown] = useState<boolean>(false);
    const [changeTaskShown, setChangeTaskShown] = useState<boolean>(false);
    const [finishTaskShown, setFinishTaskShown] = useState<boolean>(false);
    const [startTaskShown, setStartTaskShown] = useState<boolean>(false);

    const toggleTask = () => setTaskShown(!taskShown);
    const toggleChangeTask = () => setChangeTaskShown(!changeTaskShown);
    const toggleFinishTask = () => setFinishTaskShown(!finishTaskShown);
    const toggleStartTask = () => setStartTaskShown(!startTaskShown);

    let tech = props.tech;

    return (
        <>
            <div className="my-2 flex w-full flex-wrap rounded bg-white shadow py-2 px-4">
                <div className="my-2 w-full align-middle md:w-1/3">
                    <span className="mr-3 align-middle text-xl">
                        {tech.name}
                    </span>
                    <span className="align-middle text-sm text-gray-600">
                        ({tech.id})
                    </span>
                    {tech.assignedTask ? (
                        <span className="ml-8 align-middle text-sm text-gray-600">
                            zadáno mají: {tech.assignedTask.name}
                        </span>
                    ) : null}
                </div>
                <div className="flex w-full md:w-2/3">
                    {tech.status === "researching" ? (
                        <>
                            <Button
                                label="Dokončit zkoumání"
                                onClick={toggleFinishTask}
                                className="ml-0 bg-green-500 hover:bg-green-600"
                            />
                            <Button
                                label="Změnit úkol"
                                onClick={toggleChangeTask}
                                className="bg-orange-500 hover:bg-orange-600"
                            />
                            <Button
                                label={
                                    taskShown ? "Skrýt úkol" : "Zobrazit úkol"
                                }
                                onClick={toggleTask}
                                className="mr-0 bg-blue-500 hover:bg-blue-600"
                            />
                        </>
                    ) : null}
                    {tech.status === "available" ? (
                        <>
                            <Button
                                label="Začít zkoumat"
                                onClick={toggleStartTask}
                                className="ml-0 bg-green-500 hover:bg-green-600"
                            />
                        </>
                    ) : null}
                </div>
                {taskShown && tech.assignedTask ? (
                    <div className="my-2 flex w-full flex-wrap">
                        <div className="w-full md:w-1/2 md:pr-2">
                            <div className="my-2 w-full rounded bg-gray-100 p-2">
                                <h3>
                                    Zadání úkolu "{tech.assignedTask.name}" pro
                                    tým
                                </h3>
                                <CiviMarkdown>
                                    {tech.assignedTask.teamDescription}
                                </CiviMarkdown>
                            </div>
                        </div>
                        <div className="w-full md:w-1/2 md:pl-2">
                            <div className="my-2 w-full rounded bg-gray-100 p-2">
                                <h3>
                                    Zadání úkolu "{tech.assignedTask.name}" pro
                                    orga
                                </h3>
                                <CiviMarkdown>
                                    {tech.assignedTask.orgDescription}
                                </CiviMarkdown>
                            </div>
                        </div>
                    </div>
                ) : null}
            </div>
            {changeTaskShown ? (
                <Dialog onClose={toggleChangeTask}>Změnit úlohu</Dialog>
            ) : null}
            {finishTaskShown ? (
                <Dialog onClose={toggleFinishTask}>Dokončit úlohu</Dialog>
            ) : null}
            {startTaskShown ? (
                <Dialog onClose={toggleStartTask}>Začít úlohu</Dialog>
            ) : null}
        </>
    );
}
