import { Link, Navigate, Route, Routes, useParams } from "react-router-dom";
import useSWR from "swr";
import {
    Button,
    CiviMarkdown,
    Dialog,
    FormRow,
    LoadingOrError,
    Row,
} from "../elements";
import { useEntities } from "../elements/entities";
import { EditableTask, EntityTech, Task } from "../types";
import { fetcher } from "../utils/axios";
import { combineErrors } from "../utils/error";
import { Formik, Form, Field, ErrorMessage } from "formik";
import { number } from "yup";
import { useState } from "react";

export function TasksMenu() {
    return null;
}

export function Tasks() {
    return (
        <Routes>
            <Route path="" element={<TasksOverview />} />
            <Route path="new" element={<TaskEdit />} />
            <Route path="edit/:taskId" element={<TaskEdit />} />
            <Route path="*" element={<Navigate to="" />} />
        </Routes>
    );
}

function TasksOverview() {
    const { data: tasks, error: taskError } = useSWR<Task[]>(
        "game/task",
        fetcher
    );
    const {
        data: techs,
        loading: techLoading,
        error: techError,
    } = useEntities<EntityTech>("tech");

    if (!tasks || taskError || techLoading || techError || !techs)
        return (
            <LoadingOrError
                loading={techLoading || (!tasks && !taskError)}
                error={combineErrors([taskError, techError])}
                message="Nastala chyba"
            />
        );

    return (
        <>
            <h2>Přehled úkolů</h2>
            <Link to="new">
                <Button label="Nový úkol" className="mx-0 my-2 w-full" />
            </Link>
            {tasks.map((t) => (
                <TaskItem task={t} techs={techs} />
            ))}
        </>
    );
}

function TaskItem(props: { task: Task; techs: Record<string, EntityTech> }) {
    const [dDialog, setdDialog] = useState(false);

    const handleDelete = () => {
        setdDialog(false);
    };

    return (
        <div className="my-2 w-full rounded bg-white p-4 shadow">
            <Row className="flex">
                <h3 className="inline-block align-middle">{props.task.name}</h3>
                <span className="ml-4 inline-block align-middle text-gray-500">
                    ({props.task.id})
                </span>
                <Link
                    to={`edit/${props.task.id}`}
                    className="inline-block flex-auto align-middle"
                >
                    <Button
                        label="Upravit"
                        className="float-right align-middle"
                    />
                </Link>
                <Button
                    label="Smazat"
                    className="bg-red-500 hover:bg-red-600"
                    onClick={() => setdDialog(true)}
                />
            </Row>
            <Row className="flex flex-row flex-wrap">
                <div className="m-0 flex w-full flex-col p-2 md:w-1/2 md:pl-0">
                    <h2 className="font-normal text-gray-500">
                        Popis pro tým:
                    </h2>
                    <hr className="my-2" />
                    <CiviMarkdown className="grow">
                        {props.task.teamDescription}
                    </CiviMarkdown>
                    <hr className="my-2" />
                </div>
                <div className="m-0 flex w-full  flex-col p-2 md:w-1/2 md:pr-0">
                    <h2 className="font-normal text-gray-500">
                        Popis pro orga
                    </h2>
                    <hr className="my-2" />
                    <CiviMarkdown className="grow">
                        {props.task.orgDescription}
                    </CiviMarkdown>
                    <hr className="my-2" />
                </div>
            </Row>
            {dDialog ? (
                <Dialog onClose={() => setdDialog(false)}>
                    <h2>Skutečně smazat {props.task.name}?</h2>
                    <Row className="my-4 flex">
                        <Button
                            label="Ano"
                            className="flex-1"
                            onClick={handleDelete}
                        />
                        <Button
                            label="Ne"
                            className="flex-1 bg-blue-500 hover:bg-blue-600"
                            onClick={() => setdDialog(false)}
                        />
                    </Row>
                </Dialog>
            ) : null}
        </div>
    );
}

function sortTechs(techs: EntityTech[]) {
    return techs;
}

function TaskEdit() {
    const { taskId } = useParams();
    const {
        data: techs,
        loading: techLoading,
        error: techError,
    } = useEntities<EntityTech>("tech");
    const { data: task, error: taskError } = useSWR<EditableTask>(
        () => (taskId ? `game/task/${taskId}` : null),
        fetcher
    );

    if ((taskId && !task) || techError || techLoading || !techs)
        return (
            <LoadingOrError
                loading={techLoading || (!task && !taskError)}
                error={combineErrors([techError, taskError])}
                message="Nastala chyba"
            />
        );

    const handleSubmit = (data: EditableTask) => {
        console.log(data);
    };

    return (
        <>
            <Row className="mb-3 flex">
                <h1 className="block-inline align-middle">
                    {taskId ? "Editace úkolu" : "Nový úkol"}
                </h1>
                <Link
                    to={`/tasks`}
                    className="inline-block flex-auto align-middle"
                >
                    <Button
                        label="Zpět na přehled"
                        className="float-right mx-0 align-middle"
                    />
                </Link>
            </Row>
            <Formik<EditableTask>
                initialValues={
                    task
                        ? task
                        : {
                              id: "",
                              name: "",
                              teamDescription: "",
                              orgDescription: "",
                              capacity: 5,
                              occupiedCount: 0,
                              techs: [],
                          }
                }
                onSubmit={handleSubmit}
            >
                {(props) => (
                    <TaskEditForm
                        values={props.values}
                        setFieldValue={props.setFieldValue}
                        techs={sortTechs(Object.values(techs))}
                    />
                )}
            </Formik>
        </>
    );
}

function TaskEditForm(props: {
    values: EditableTask;
    setFieldValue: (field: string, value: any, validate: boolean) => void;
    techs: EntityTech[];
}) {
    const allTechs = () => {
        props.setFieldValue(
            "techs",
            props.techs.map((x) => x.id),
            false
        );
    };
    const noTechs = () => {
        props.setFieldValue("techs", [], false);
    };
    return (
        <div className="w-full">
            <Form {...props}>
                <FormRow
                    label="Název úkolu"
                    error={<ErrorMessage name="name" />}
                >
                    <Field name="name" />
                </FormRow>
                <FormRow
                    label="Kapacita"
                    error={<ErrorMessage name="capacity" />}
                >
                    <Field name="capacity" type="number" />
                </FormRow>
                <FormRow
                    label="Popis pro tým"
                    error={<ErrorMessage name="teamDescription" />}
                >
                    <Field name="teamDescription" as="textarea" rows={8} />
                </FormRow>
                <FormRow label="Náhled popisu pro tým:">
                    <div className="w-full rounded bg-white p-4 shadow">
                        <CiviMarkdown>
                            {props.values.teamDescription}
                        </CiviMarkdown>
                    </div>
                </FormRow>
                <FormRow
                    label="Popis pro orga"
                    error={<ErrorMessage name="orgDescription" />}
                >
                    <Field name="orgDescription" as="textarea" rows={8} />
                </FormRow>
                <FormRow label="Náhled popisu pro orga:">
                    <div className="w-full rounded bg-white p-4 shadow">
                        <CiviMarkdown>
                            {props.values.orgDescription}
                        </CiviMarkdown>
                    </div>
                </FormRow>
                <FormRow
                    label="Přiřazen následujícím technologiím:"
                    error={<ErrorMessage name="techs" />}
                    extra={
                        <div className="flex w-full flex-row-reverse px-0">
                            <Button
                                label="Označit vše"
                                className="m-0 mr-2 grow"
                                onClick={allTechs}
                            />
                            <Button
                                label="Nic neoznačit"
                                className="m-0 ml-2 grow"
                                onClick={noTechs}
                            />
                        </div>
                    }
                >
                    <div className="flex w-full flex-row flex-wrap">
                        {props.techs.map((t) => (
                            <div
                                className="m-2 grow rounded bg-white p-2 shadow"
                                key={t.id}
                            >
                                <Field
                                    type="checkbox"
                                    name="techs"
                                    value={t.id}
                                    className="checkboxinput align-middle"
                                />
                                <label className="mx-3 align-middle">
                                    {t.name}
                                </label>
                            </div>
                        ))}
                    </div>
                </FormRow>
                <Button
                    className="my-5 w-full bg-purple-500 hover:bg-purple-600"
                    type="submit"
                    label={
                        props.values.id ? "Uložit změny" : "Založit nový úkol"
                    }
                />
            </Form>
        </div>
    );
}
