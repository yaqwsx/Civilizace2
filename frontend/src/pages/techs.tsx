import _ from "lodash";
import { ChangeEvent, useState } from "react";
import { toast } from "react-toastify";
import {
    Button,
    CiviMarkdown,
    Dialog,
    FormRow,
    LoadingOrError,
} from "../elements";
import { PerformAction } from "../elements/action";
import {
    TeamRowIndicator,
    TeamSelector,
    useTeamFromUrl,
} from "../elements/team";
import {
    changeTeamTask,
    useTeamEntities,
    useTeamTasks,
} from "../elements/team_view";
import {
    Task,
    Team,
    TechEntity,
    TechOrgTeamEntity,
    TechStatus,
} from "../types";
import { useHideMenu } from "./atoms";

export function TechMenu() {
    return null;
}

export function Tech() {
    useHideMenu();
    const { team, setTeam, error, success } = useTeamFromUrl();

    if (!success) {
        return <LoadingOrError error={error} message={"Nemůžu načíst týmy"} />;
    }

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
                <TeamSelector onChange={handleTeamChange} activeId={team?.id} />
            </FormRow>
            <TeamRowIndicator team={team ?? undefined} />
            {team ? <TechListing team={team} /> : null}
        </>
    );
}

export function sortTechs<TTechEntity extends TechEntity>(
    techs: TTechEntity[]
) {
    return _.sortBy(
        techs,
        (t) => !t.requiresTask,
        (t) => t.name,
        (t) => t.id
    );
}

function TechListing(props: { team: Team }) {
    const {
        data: techs,
        error,
        mutate,
    } = useTeamEntities<TechOrgTeamEntity>("techs", props.team);

    if (!techs)
        return (
            <LoadingOrError
                error={error}
                message={"Nemůžu načíst technologie pro tým."}
            />
        );

    return (
        <>
            <h2>{props.team.name} aktuálně zkoumají:</h2>
            <TechList
                team={props.team}
                techs={Object.values(techs).filter(
                    (t) => t.status === TechStatus.Researching
                )}
                onTaskMutation={mutate}
                emptyMessage={`Tým ${props.team.name} nic nezkoumá.`}
            />
            <h2>{props.team.name} mohou začít zkoumat:</h2>
            <h3>Velké technologie:</h3>
            <TechList
                team={props.team}
                techs={Object.values(techs).filter(
                    (t) => t.status === TechStatus.Available && t.requiresTask
                )}
                onTaskMutation={mutate}
                emptyMessage={`Tým ${props.team.name} nemůže nic zkoumat. Ten je ale drsný nebo je to bug.`}
            />
            <h3>Malé technologie:</h3>
            <TechList
                team={props.team}
                techs={Object.values(techs).filter(
                    (t) => t.status === TechStatus.Available && !t.requiresTask
                )}
                onTaskMutation={mutate}
                emptyMessage={`Tým ${props.team.name} nemůže nic zkoumat.`}
            />
            <h2>{props.team.name} mají vyzkoumáno:</h2>
            <h3>Velké technologie:</h3>
            <TechList
                team={props.team}
                techs={Object.values(techs).filter(
                    (t) => t.status === TechStatus.Owned && t.requiresTask
                )}
                onTaskMutation={mutate}
                emptyMessage={`Tým ${props.team.name} nevlastní žádné velké technologie. Což je asi bug.`}
            />
            <h3>Malé technologie:</h3>
            <TechList
                team={props.team}
                techs={Object.values(techs).filter(
                    (t) => t.status === TechStatus.Owned && !t.requiresTask
                )}
                onTaskMutation={mutate}
                emptyMessage={`Tým ${props.team.name} ještě nevlastní žádné malé technologie.`}
            />
        </>
    );
}

function TechList(props: {
    team: Team;
    techs: TechOrgTeamEntity[];
    onTaskMutation: () => void;
    emptyMessage?: string;
}) {
    if (props.techs.length == 0) {
        return <p>{props.emptyMessage}</p>;
    }

    return (
        <div className="pl-4">
            {sortTechs(props.techs).map((t) => (
                <TechItem
                    key={t.id}
                    team={props.team}
                    tech={t}
                    onTaskMutation={props.onTaskMutation}
                    error={
                        t.assignedTask &&
                        (!t.requiresTask || t.status != TechStatus.Researching)
                            ? "Tech má přiřazaný úkol, což je asi bug"
                            : undefined
                    }
                />
            ))}
        </div>
    );
}

function TechActions(props: {
    tech: TechOrgTeamEntity;
    onStartResearch: () => void;
    onFinishTask: () => void;
    onChangeTask: () => void;
    showTask: boolean;
    toggleShowTask: () => void;
}) {
    switch (props.tech.status) {
        case TechStatus.Researching:
            return (
                <>
                    <Button
                        label="Dokončit zkoumání"
                        onClick={props.onFinishTask}
                        className="ml-0 bg-green-500 hover:bg-green-600"
                    />
                    <Button
                        label="Změnit úkol"
                        onClick={props.onChangeTask}
                        className="bg-orange-500 hover:bg-orange-600"
                    />
                    <Button
                        label={
                            props.tech.assignedTask
                                ? props.showTask
                                    ? "Skrýt úkol"
                                    : "Zobrazit úkol"
                                : "Nebyl zadán úkol"
                        }
                        onClick={props.toggleShowTask}
                        className="mr-0 bg-blue-500 hover:bg-blue-600"
                        disabled={!props.tech.assignedTask}
                    />
                </>
            );

        case TechStatus.Available:
            return (
                <>
                    <Button
                        label={
                            props.tech.requiresTask
                                ? "Začít zkoumat"
                                : "Vyzkoumat"
                        }
                        onClick={props.onStartResearch}
                        className="ml-0 bg-green-500 hover:bg-green-600"
                    />
                </>
            );

        case TechStatus.Owned:
            return <></>;
        default:
            const exhaustiveCheck: never = props.tech.status;
            return <></>; // For invalid Enum value
    }
}

function ExtendedTaskView(props: { tech: TechOrgTeamEntity }) {
    return props.tech.assignedTask ? (
        <div className="my-2 flex w-full flex-wrap">
            <div className="w-full md:w-1/2 md:pr-2">
                <div className="my-2 w-full rounded bg-gray-100 p-2">
                    <h3>
                        Zadání úkolu "{props.tech.assignedTask.name}" pro tým
                    </h3>
                    <CiviMarkdown>
                        {props.tech.assignedTask.teamDescription}
                    </CiviMarkdown>
                </div>
            </div>
            <div className="w-full md:w-1/2 md:pl-2">
                <div className="my-2 w-full rounded bg-gray-100 p-2">
                    <h3>
                        Zadání úkolu "{props.tech.assignedTask.name}" pro orga
                    </h3>
                    <CiviMarkdown>
                        {props.tech.assignedTask.orgDescription}
                    </CiviMarkdown>
                </div>
            </div>
        </div>
    ) : (
        <p className="my-3 w-full text-center">Nebyl zadán žádný úkol</p>
    );
}

enum TechDialogType {
    ChangeTask,
    FinishTask,
    StartResearching,
}

function TechDialog(props: {
    type: TechDialogType | undefined;
    team: Team;
    tech: TechOrgTeamEntity;
    onClose: () => void;
}) {
    switch (props.type) {
        case undefined:
            return <></>;
        case TechDialogType.ChangeTask:
            return (
                <ChangeTaskDialog
                    team={props.team}
                    tech={props.tech}
                    onClose={props.onClose}
                />
            );
        case TechDialogType.FinishTask:
            return (
                <FinishTaskDialog
                    team={props.team}
                    tech={props.tech}
                    onClose={props.onClose}
                />
            );
        case TechDialogType.StartResearching:
            return (
                <StartResearchingDialog
                    team={props.team}
                    tech={props.tech}
                    onClose={props.onClose}
                />
            );
    }
}

function TechItem(props: {
    team: Team;
    tech: TechOrgTeamEntity;
    onTaskMutation: () => void;
    error?: any;
}) {
    const [showTask, setShowTask] = useState(false);
    const [shownDialog, setShownDialog] = useState<TechDialogType>();

    return (
        <>
            <div className="my-2 flex w-full flex-wrap rounded bg-white py-2 px-4 shadow">
                <div className="my-2 w-full align-middle md:w-1/3">
                    <span className="mr-3 align-middle text-xl">
                        {props.tech.name}
                    </span>
                    <span className="align-middle text-sm text-gray-600">
                        ({props.tech.id})
                    </span>
                    {props.tech.assignedTask ? (
                        <span className="ml-8 align-middle text-sm text-gray-600">
                            zadáno mají: {props.tech.assignedTask.name}
                        </span>
                    ) : null}
                    <div className="ml-4 block w-full text-red-600">
                        {props.error}
                    </div>
                </div>
                <div className="flex w-full md:w-2/3">
                    <TechActions
                        tech={props.tech}
                        onStartResearch={() =>
                            setShownDialog(TechDialogType.StartResearching)
                        }
                        onFinishTask={() =>
                            setShownDialog(TechDialogType.FinishTask)
                        }
                        onChangeTask={() =>
                            setShownDialog(TechDialogType.ChangeTask)
                        }
                        showTask={showTask}
                        toggleShowTask={() => setShowTask((value) => !value)}
                    />
                </div>
                {showTask ? <ExtendedTaskView tech={props.tech} /> : null}
            </div>
            <TechDialog
                type={shownDialog}
                team={props.team}
                tech={props.tech}
                onClose={() => {
                    setShownDialog(undefined);
                    props.onTaskMutation();
                }}
            />
        </>
    );
}

function TaskSelectInfo(props: { team: Team; task: Task }) {
    const teamAssignments = props.task.assignments.filter(
        (a) => a.team === props.team.id
    );
    const active = teamAssignments.some((a) => !a.finishedAt);
    const finished = teamAssignments.some((a) => a.finishedAt && !a.abandoned);
    const abandoned = teamAssignments.some((a) => a.finishedAt && a.abandoned);
    console.log("assignments", props.task.name, {
        task: props.task,
        teamAssignments,
        active,
        finished,
        abandoned,
    });
    return (
        `${props.task.id}: ${props.task.name} (${props.task.occupiedCount}/${props.task.capacity})` +
        (finished
            ? ` - ${props.team.name} už úkol absolvovali`
            : active
            ? ` - ${props.team.name} už mají úkol aktivní`
            : abandoned
            ? ` - ${props.team.name} už úkol dostali zadaný (a neuspěli)`
            : "")
    );
}

function SelectTask(props: {
    team: Team;
    tasks: Task[];
    selectedTask: Task | undefined;
    onChange: (task: Task | undefined) => void;
}) {
    const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
        props.onChange(props.tasks.find((t) => t.id === event.target.value));
    };

    return (
        <select
            value={props.selectedTask?.id ?? ""}
            onChange={handleChange}
            className="select"
        >
            <option value="">Nevybráno</option>
            {props.tasks
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((t) => (
                    <option key={t.id} value={t.id}>
                        {TaskSelectInfo({ team: props.team, task: t })}
                    </option>
                ))}
        </select>
    );
}

function SelectTaskForTechForm(props: {
    team: Team;
    tech: TechEntity;
    selectedTask?: Task;
    onChange: (t: Task | undefined) => void;
}) {
    const { data: tasks, error: taskError } = useTeamTasks(props.team);

    if (!tasks) {
        return (
            <LoadingOrError
                error={taskError}
                message={"Nemůžu načíst úkoly ze serveru. Zkouším znovu"}
            />
        );
    }

    const recommendedTechs = Object.values(tasks).filter((t) => {
        if (t.occupiedCount >= t.capacity) return false;
        if (!t.techs?.includes(props.tech.id)) return false;
        if (
            t.assignments
                .filter((a) => a.team === props.team.id)
                .filter((a) => a.techId !== props.tech.id).length > 0
        )
            return false;
        return true;
    });

    console.log(
        "t.occupiedCount >= t.capacity",
        Object.values(tasks).filter((t) => t.occupiedCount >= t.capacity)
    );
    console.log(
        "!t.techs?.includes(props.tech.id)",
        Object.values(tasks).filter((t) => !t.techs?.includes(props.tech.id))
    );
    console.log(
        "t.assignments.map((x) => x.team).includes(props.team.id)",
        Object.values(tasks).filter((t) =>
            t.assignments.map((x) => x.team).includes(props.team.id)
        )
    );

    const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
        props.onChange(tasks[event.target.value]);
    };

    return (
        <>
            <FormRow label="Doporučené úkoly">
                <SelectTask
                    team={props.team}
                    tasks={recommendedTechs}
                    selectedTask={props.selectedTask}
                    onChange={props.onChange}
                />
            </FormRow>
            <FormRow label="Všechny úkoly (pokud doporučený nevyhovuje)">
                <SelectTask
                    team={props.team}
                    tasks={Object.values(tasks)}
                    selectedTask={props.selectedTask}
                    onChange={props.onChange}
                />
            </FormRow>
            <FormRow label="Popis pro orga">
                <CiviMarkdown>
                    {props.selectedTask?.orgDescription ?? ""}
                </CiviMarkdown>
            </FormRow>
            <FormRow label="Popis pro účastníky">
                <CiviMarkdown>
                    {props.selectedTask?.teamDescription ?? ""}
                </CiviMarkdown>
            </FormRow>
        </>
    );
}

function StartResearchingDialog(props: {
    team: Team;
    tech: TechOrgTeamEntity;
    onClose: () => void;
}) {
    const [selectedTask, setSelectedTask] = useState<Task>();

    return (
        <Dialog onClose={props.onClose}>
            <PerformAction
                actionName={
                    props.tech.requiresTask
                        ? `Začít zkoumat ${props.tech.name} pro ${props.team.name}`
                        : `Vyzkoumat ${props.tech.name} pro ${props.team.name}`
                }
                actionId="ResearchStartAction"
                actionArgs={{
                    tech: props.tech.id,
                    team: props.team.id,
                    task: selectedTask?.id,
                }}
                extraPreview={
                    props.tech.requiresTask ? (
                        <>
                            <h1>Vyberte úkol</h1>
                            <SelectTaskForTechForm
                                team={props.team}
                                tech={props.tech}
                                selectedTask={selectedTask}
                                onChange={(t) => setSelectedTask(t)}
                            />
                        </>
                    ) : undefined
                }
                onFinish={props.onClose}
                onBack={props.onClose}
            />
        </Dialog>
    );
}

function ChangeTaskDialog(props: {
    tech: TechOrgTeamEntity;
    team: Team;
    onClose: () => void;
}) {
    const [selectedTask, setSelectedTask] = useState<Task>();
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = () => {
        setSubmitting(true);
        changeTeamTask(props.team, {
            tech: props.tech.id,
            newTask: selectedTask?.id ?? null,
        })
            .then(() => {
                setSubmitting(false);
                toast.success("Úkol změněn");
                props.onClose();
            })
            .catch((error) => {
                console.error("Change task:", error);
                setSubmitting(false);
                toast.error(`Nastala neočekávaná chyba: ${error}`);
            });
    };

    return (
        <Dialog onClose={props.onClose}>
            <h1>Změnit úlohu</h1>
            Aktuální úkol:{" "}
            {props.tech.assignedTask
                ? `${props.tech.assignedTask.id} (${props.tech.assignedTask.name})`
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
        </Dialog>
    );
}

function FinishTaskDialog(props: {
    team: Team;
    tech: TechOrgTeamEntity;
    onClose: () => void;
}) {
    return (
        <Dialog onClose={props.onClose}>
            <PerformAction
                actionName={`Dokončit zkoumání ${props.tech.name} pro ${props.team.name}`}
                actionId="ResearchFinishAction"
                actionArgs={{
                    tech: props.tech.id,
                    team: props.team.id,
                }}
                onFinish={props.onClose}
                onBack={props.onClose}
            />
        </Dialog>
    );
}
