import { Props } from "@fortawesome/react-fontawesome";
import classNames from "classnames";
import { ChangeEvent, useState } from "react";
import { toast } from "react-toastify";
import useSWR, { mutate } from "swr";
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
import { PerformAction } from "../elements/action";
import { useTeamTechs } from "../elements/entities";
import {
    useTeamFromUrl,
    TeamSelector,
    TeamRowIndicator,
} from "../elements/team";
import { EntityTech, Task, Team, TeamEntityTech } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { useHideMenu } from "./atoms";
import { useEditableTasks } from "./tasks";

export function TechMenu() {
    return null;
}

export function Tech() {
    useHideMenu();
    const { team, setTeam, loading, error } = useTeamFromUrl();

    if (loading || error)
        return (
            <LoadingOrError
                loading={loading}
                error={error}
                message={"Nemůžu načíst týmy"}
            />
        );

    const handleTeamChange = (t?: Team) => {
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

export function sortTechs(techs: TeamEntityTech[]) {
    // TBA
    return techs;
}

function TechListing(props: { team: Team }) {
    const { techs, loading, error, mutate } = useTeamTechs(props.team);

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

    return (
        <>
            <h2>{props.team.name} aktuálně zkoumají:</h2>
            {researchingTechs ? (
                <TechList
                    team={props.team}
                    techs={researchingTechs}
                    onTaskMutation={mutate}
                />
            ) : (
                <p>Tým {props.team.name} nic nezkoumá.</p>
            )}
            <h2>{props.team.name} mohou začít zkoumat:</h2>
            {availableTechs ? (
                <TechList
                    team={props.team}
                    techs={availableTechs}
                    onTaskMutation={mutate}
                />
            ) : (
                <p>
                    Tým {props.team.name} nemůže nic zkoumat. Ten je ale drný
                    nebo je to bug
                </p>
            )}
            <h2>{props.team.name} mají vyzkoumáno:</h2>
            {ownedTechs ? (
                <TechList
                    team={props.team}
                    techs={ownedTechs}
                    onTaskMutation={mutate}
                />
            ) : (
                <p>
                    Tým {props.team.name} nevlastní žádné technologie. Což je
                    asi bug.
                </p>
            )}
        </>
    );
}

function TechList(props: {
    team: Team;
    techs: TeamEntityTech[];
    onTaskMutation: () => void;
}) {
    return (
        <div className="pl-4">
            {props.techs.map((t) => (
                <TechItem
                    key={t.id}
                    team={props.team}
                    tech={t}
                    onTaskMutation={props.onTaskMutation}
                />
            ))}
        </div>
    );
}

function TechItem(props: {
    team: Team;
    tech: TeamEntityTech;
    onTaskMutation: () => void;
}) {
    const [taskShown, setTaskShown] = useState<boolean>(false);
    const [changeTaskShown, setChangeTaskShown] = useState<boolean>(false);
    const [finishTaskShown, setFinishTaskShown] = useState<boolean>(false);
    const [startTaskShown, setStartTaskShown] = useState<boolean>(false);
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);

    const toggleTask = () => setTaskShown(!taskShown);
    const toggleChangeTask = () => {
        setSelectedTask(null);
        setChangeTaskShown(!changeTaskShown);
    };
    const toggleFinishTask = () => {
        setSelectedTask(null);
        setFinishTaskShown(!finishTaskShown);
    };
    const toggleStartTask = () => {
        setSelectedTask(null);
        setStartTaskShown(!startTaskShown);
    };

    let tech = props.tech;

    return (
        <>
            <div className="my-2 flex w-full flex-wrap rounded bg-white py-2 px-4 shadow">
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
                                    tech?.assignedTask
                                        ? taskShown
                                            ? "Skrýt úkol"
                                            : "Zobrazit úkol"
                                        : "Nebyl zadán úkol"
                                }
                                onClick={toggleTask}
                                className="mr-0 bg-blue-500 hover:bg-blue-600"
                                disabled={!tech?.assignedTask}
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
                {taskShown && !tech.assignedTask ? (
                    <p className="my-3 w-full text-center">
                        Nebyl zadán žádný úkol
                    </p>
                ) : null}
            </div>
            {changeTaskShown ? (
                <Dialog onClose={toggleChangeTask}>
                    <ChangeTaskDialog
                        team={props.team}
                        tech={tech}
                        mutateTechs={props.onTaskMutation}
                        onClose={toggleChangeTask}
                    />
                </Dialog>
            ) : null}
            {finishTaskShown ? (
                <Dialog onClose={toggleFinishTask}>
                    <PerformAction
                        actionName={`Dokončit zkoumání ${tech.name} pro ${props.team.name}`}
                        actionId="ActionResearchFinish"
                        actionArgs={{
                            tech: tech.id,
                            team: props.team.id,
                        }}
                        onFinish={() => {
                            toggleFinishTask();
                            props.onTaskMutation();
                        }}
                        onBack={toggleFinishTask}
                        team={props.team}
                    />
                </Dialog>
            ) : null}
            {startTaskShown ? (
                <Dialog onClose={toggleStartTask}>
                    <PerformAction
                        actionName={`Začít zkoumat ${tech.name} pro ${props.team.name}`}
                        actionId="ActionResearchStart"
                        actionArgs={{
                            tech: tech.id,
                            team: props.team.id,
                            task: selectedTask ? selectedTask.id : null,
                        }}
                        extraPreview={
                            <>
                                <h1>Vyberte úkol</h1>
                                <SelectTaskForTechForm
                                    team={props.team}
                                    tech={tech}
                                    selectedTask={selectedTask}
                                    onChange={(t) => setSelectedTask(t)}
                                />
                            </>
                        }
                        onFinish={() => {
                            toggleStartTask();
                            props.onTaskMutation();
                        }}
                        onBack={toggleStartTask}
                        team={props.team}
                    />
                </Dialog>
            ) : null}
        </>
    );
}

function TaskSelectRow(props: { team: Team; task: Task }) {
    let assigned = false;
    props.task.assignments.forEach((x) => {
        if (x.team == props.team.id) assigned = true;
    });
    return (
        <option value={props.task.id}>
            {props.task.id}: {props.task.name}({props.task.occupiedCount}/
            {props.task.capacity})
            {assigned ? ` ${props.team.name} už úkol absolvovali` : ""}
        </option>
    );
}

function SelectTaskForTechForm(props: {
    team: Team;
    tech: EntityTech;
    selectedTask: Task | null;
    onChange: (t: Task) => void;
}) {
    const { data: tasks, error: taskError } = useSWR<Record<string, Task>>(
        `/game/teams/${props.team.id}/tasks`,
        fetcher
    );

    if (!tasks) {
        return (
            <LoadingOrError
                loading={!taskError && !tasks}
                error={taskError}
                message={"Nemůžu načíst úkoly ze serveru. Zkouším znovu"}
            />
        );
    }

    let recommendedTechs = Object.values(tasks).filter((t) => {
        if (t.occupiedCount >= t.capacity) return false;
        if (!t.techs?.includes(props.tech.id)) return false;
        if (t.assignments.map((x) => x.team).includes(props.team.id))
            return false;
        return true;
    });

    const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
        props.onChange(tasks[event.target.value]);
    };

    return (
        <>
            <FormRow label="Doporučené úkoly">
                <select
                    value={String(props.selectedTask?.id)}
                    onChange={handleChange}
                    className="select"
                >
                    <option>Nevybráno</option>
                    {recommendedTechs.map((t) => (
                        <TaskSelectRow key={t.id} team={props.team} task={t} />
                    ))}
                </select>
            </FormRow>
            <FormRow label="Všechny úkoly (pokud doporučený nevyhovuje)">
                <select
                    value={String(props.selectedTask?.id)}
                    onChange={handleChange}
                    className="select"
                >
                    <option>Nevybráno</option>
                    {Object.values(tasks).map((t) => (
                        <TaskSelectRow key={t.id} team={props.team} task={t} />
                    ))}
                </select>
            </FormRow>
            <FormRow label="Popis pro orga">
                {props.selectedTask && (
                    <CiviMarkdown>
                        {props.selectedTask.orgDescription}
                    </CiviMarkdown>
                )}
            </FormRow>
            <FormRow label="Popis pro účastníky">
                {props.selectedTask && (
                    <CiviMarkdown>
                        {props.selectedTask.teamDescription}
                    </CiviMarkdown>
                )}
            </FormRow>
        </>
    );
}

function ChangeTaskDialog(props: {
    tech: TeamEntityTech;
    team: Team;
    mutateTechs: () => void;
    onClose: () => void;
}) {
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);
    const [submitting, setSubmitting] = useState(false);

    let handleSubmit = () => {
        setSubmitting(true);
        axiosService
            .post<any, any>(`/game/teams/${props.team.id}/changetask/`, {
                tech: props.tech.id,
                newTask: selectedTask ? selectedTask?.id : null,
            })
            .then(() => {
                setSubmitting(false);
                toast.success("Úkol změněn");
                props.mutateTechs();
                props.onClose();
            })
            .catch((error) => {
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };

    return (
        <>
            <h1>Změnit úlohu</h1>
            Aktuální úkol:{" "}
            {props.tech.assignedTask
                ? `${props.tech.assignedTask} (${props.tech.assignedTask.name})`
                : "Žádný úkol"}
            <SelectTaskForTechForm
                team={props.team}
                tech={props.tech}
                selectedTask={selectedTask}
                onChange={(t) => setSelectedTask(t)}
            />
            <Button
                label={submitting ? "Odesílám" : "Změnit úkol"}
                className="w-full"
                disabled={submitting}
                onClick={handleSubmit}
            />
        </>
    );
}
