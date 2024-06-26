import classNames from "classnames";
import { ErrorMessage, Field, Form, Formik, FormikHelpers } from "formik";
import _ from "lodash";
import { useState } from "react";
import DateTime from "react-datetime";
import "react-datetime/css/react-datetime.css";
import {
    Link,
    Navigate,
    Route,
    Routes,
    useNavigate,
    useParams,
} from "react-router-dom";
import { toast } from "react-toastify";
import useSWR from "swr";
import {
    Button,
    CiviMarkdown,
    Dialog,
    FormRow,
    LoadingOrError,
    Row,
} from "../elements";
import { useTeams } from "../elements/team";
import { Announcement, AnnouncementType, Team } from "../types";
import axiosService, { fetcher } from "../utils/axios";
import { objectMap } from "../utils/functional";
import { useHideMenu } from "./atoms";

export function AnnouncementsMenu() {
    return null;
}

export function Announcements() {
    useHideMenu();

    return (
        <Routes>
            <Route path="" element={<AnnouncementsOverview />} />
            <Route path="new" element={<AnnouncementEdit />} />
            <Route path="edit/:announcementId" element={<AnnouncementEdit />} />
            <Route path="*" element={<Navigate to="" />} />
        </Routes>
    );
}

function AnnouncementsOverview() {
    const {
        data: announcements,
        error,
        mutate: mutateAnnouncements,
    } = useSWR<Announcement[]>("/announcements", fetcher);
    const { teams, error: teamError } = useTeams();

    if (!announcements || !teams)
        return (
            <LoadingOrError
                error={error || teamError}
                message="Nastala chyba"
            />
        );

    const handleDelete = (id: number) => {
        const options = {
            optimisticData: announcements?.filter((x) => x.id != id),
        };
        const fetchNew = async () => {
            return fetcher<Announcement[]>("/announcements");
        };
        mutateAnnouncements(fetchNew, options);
    };

    return (
        <>
            <h2>Správa vývěsky</h2>
            <Link to="new">
                <Button label="Nové oznámení" className="mx-0 my-2 w-full" />
            </Link>
            {announcements.map((a) => (
                <AnnouncementItem
                    key={a.id}
                    announcement={a}
                    teams={teams}
                    onDelete={() => handleDelete(a.id)}
                />
            ))}
        </>
    );
}

function translateAnnouncementType(type: AnnouncementType) {
    switch (type) {
        case AnnouncementType.Important:
            return "Důležité";
        case AnnouncementType.Normal:
            return "Normání";
        case AnnouncementType.Game:
            return "Systémové";
        default:
            const exhaustiveCheck: never = type;
            return ""; // For invalid Enum value
    }
}

function AnnouncementItem(props: {
    announcement: Announcement;
    teams: Team[];
    onDelete: () => void;
}) {
    const [dDialog, setdDialog] = useState(false);

    const handleDelete = () => {
        setdDialog(false);
    };

    return (
        <div className="my-2 w-full rounded bg-white p-4 shadow">
            <Row className="flex">
                <h3 className="inline-block align-middle">
                    Oznámení {props.announcement.id}
                </h3>
                <Link
                    to={`edit/${props.announcement.id}`}
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
            <Row>
                <FormRow label="Naposledy upravil:" className="mb-0">
                    <p>{props.announcement?.author}</p>
                </FormRow>
                <FormRow label="Viditelné od:" className="mb-0">
                    <p>
                        {new Date(
                            props.announcement.appearDatetime
                        ).toLocaleString("cs-CZ")}
                    </p>
                </FormRow>
                <FormRow label="Důležitost:" className="mb-0">
                    {translateAnnouncementType(props.announcement.type)}
                </FormRow>
                <FormRow label="Obsah:" className="mb-0">
                    <CiviMarkdown>{props.announcement.content}</CiviMarkdown>
                </FormRow>
                <FormRow label="Viditelné pro:" className="mb-0">
                    <div className="flex w-full flex-row flex-wrap">
                        {props.teams.map((team) => {
                            if (!props.announcement.teams.includes(team.id))
                                return null;
                            return (
                                <div
                                    key={team.id}
                                    className={classNames(
                                        "flex-none",
                                        "w-6",
                                        "h-6",
                                        "rounded",
                                        "m-1",
                                        "bg-" + team.color
                                    )}
                                >
                                    &nbsp;
                                </div>
                            );
                        })}
                    </div>
                </FormRow>
            </Row>
            {dDialog ? (
                <DeleteDialog
                    close={() => setdDialog(false)}
                    announcement={props.announcement}
                    onDelete={props.onDelete}
                />
            ) : null}
        </div>
    );
}

function DeleteDialog(props: {
    close: () => void;
    announcement: Announcement;
    onDelete: () => void;
}) {
    const [deleting, setDeleting] = useState(false);

    const handleDelete = () => {
        setDeleting(true);
        axiosService
            .delete(`/announcements/${props.announcement.id}/`)
            .then(() => {
                props.onDelete();
                props.close();
                toast.success("Smazáno");
            })
            .catch((error) => {
                if (error?.response?.status === "403") {
                    console.warn(
                        "Delete announcement:",
                        error.response.data,
                        error
                    );
                    toast.error(error.response.data.detail);
                } else {
                    console.error("Delete announcement:", error);
                    toast.error(`Nastala neočekávaná chyba: ${error}`);
                }
            })
            .finally(() => {
                props.close();
            });
    };

    return (
        <Dialog onClose={props.close}>
            <h2>Skutečně smazat oznámení {props.announcement.id}?</h2>
            <Row className="my-4 flex">
                <Button
                    disabled={deleting}
                    className="flex-1"
                    onClick={handleDelete}
                    label={deleting ? "Mažu, prosím čekejte" : "Ano"}
                />
                <Button
                    disabled={deleting}
                    label="Ne"
                    className="flex-1 bg-blue-500 hover:bg-blue-600"
                    onClick={props.close}
                />
            </Row>
        </Dialog>
    );
}

function AnnouncementEdit() {
    const { announcementId } = useParams();
    const navigate = useNavigate();
    const { teams, error: teamError } = useTeams();
    const { data: announcement, error: announcementError } =
        useSWR<Announcement>(
            () => (announcementId ? `/announcements/${announcementId}` : null),
            fetcher
        );

    if ((announcementId && !announcement) || !teams)
        return (
            <LoadingOrError
                error={announcementError || teamError}
                message="Nastala chyba"
            />
        );

    const handleSubmit = (
        data: Omit<Announcement, "id">,
        {
            setErrors,
            setStatus,
            setSubmitting,
        }: FormikHelpers<Omit<Announcement, "id">>
    ) => {
        console.log("Submit:", data);
        setSubmitting(true);

        let submit = announcementId
            ? (data: Omit<Announcement, "id">) =>
                  axiosService.put<Announcement>(
                      `/announcements/${announcementId}/`,
                      data
                  )
            : (data: Omit<Announcement, "id">) =>
                  axiosService.post<Announcement>(`/announcements/`, data);
        submit(data)
            .then((response) => {
                navigate("/announcements");
                toast.success("Oznámení uloženo");
            })
            .catch((e) => {
                if (e.response.status == 400) {
                    console.warn("Announcement - chyba ve formuláři:", e);
                    setErrors(
                        objectMap(e.response.data, (errors) =>
                            errors.join(", ")
                        )
                    );
                    toast.error(
                        "Formulář obsahuje chyby, založení úkolu se nezdařilo. Opravte chyby a opakujte."
                    );
                } else {
                    console.error("Announcement:", e);
                    setStatus(e.toString());
                    toast.error(e.toString());
                }
            })
            .finally(() => {
                setSubmitting(false);
            });
    };

    const initialValues: Omit<Announcement, "id"> = {
        author: undefined,
        type: AnnouncementType.Normal,
        content: "",
        appearDatetime: new Date(),
        teams: [],
    };

    return (
        <>
            <Row className="mb-3 flex">
                <h1 className="block-inline align-middle">
                    {announcementId ? "Editace oznámení" : "Nové oznámení"}
                </h1>
                <Link
                    to={`/announcements`}
                    className="inline-block flex-auto align-middle"
                >
                    <Button
                        label="Zpět na přehled"
                        className="float-right mx-0 align-middle"
                    />
                </Link>
            </Row>
            <Formik<Omit<Announcement, "id">>
                initialValues={announcement ?? initialValues}
                onSubmit={handleSubmit}
            >
                {(props) => (
                    <AnnouncementEditForm
                        values={props.values}
                        setFieldValue={props.setFieldValue}
                        teams={teams}
                        creatingNew={_.isNil(announcementId)}
                        submitting={props.isSubmitting}
                    />
                )}
            </Formik>
        </>
    );
}

function AnnouncementEditForm(props: {
    values: Omit<Announcement, "id">;
    setFieldValue: (field: string, value: any, validate: boolean) => void;
    teams: Team[];
    creatingNew: boolean;
    submitting: boolean;
}) {
    const allTeams = () => {
        props.setFieldValue(
            "teams",
            props.teams.map((x) => x.id),
            false
        );
    };
    const noTeams = () => {
        props.setFieldValue("teams", [], false);
    };
    const { submitting, setFieldValue, creatingNew, ...otherProps } = props;
    return (
        <div className="w-full">
            <Form {...otherProps}>
                <FormRow
                    label="Viditelné od:"
                    error={<ErrorMessage name="appearDatetime" />}
                >
                    <DateTime
                        className="w-full"
                        dateFormat="D. M."
                        timeFormat="H:mm"
                        value={props.values.appearDatetime}
                        onChange={(date) =>
                            props.setFieldValue("appearDatetime", date, true)
                        }
                    />
                </FormRow>
                <FormRow label="Typ:" error={<ErrorMessage name="type" />}>
                    <select
                        className="select"
                        value={props.values.type ?? ""}
                        onChange={(e) =>
                            props.setFieldValue("type", e.target.value, true)
                        }
                    >
                        {Object.values(AnnouncementType)
                            .filter((t) => t != AnnouncementType.Game)
                            .map((t) => (
                                <option key={t} value={t}>
                                    {translateAnnouncementType(t)}
                                </option>
                            ))}
                    </select>
                </FormRow>
                <FormRow
                    label="Zpráva:"
                    error={<ErrorMessage name="content" />}
                >
                    <Field name="content" as="textarea" rows={8} />
                </FormRow>
                <FormRow label="Náhled zprávy:">
                    <div className="w-full rounded bg-white p-4 shadow">
                        <CiviMarkdown>{props.values.content}</CiviMarkdown>
                    </div>
                </FormRow>
                <FormRow
                    label="Viditelné pro týmy:"
                    error={<ErrorMessage name="teams" />}
                    extra={
                        <div className="flex w-full flex-row-reverse px-0">
                            <Button
                                label="Označit vše"
                                className="m-0 mr-2 grow"
                                onClick={allTeams}
                            />
                            <Button
                                label="Nic neoznačit"
                                className="m-0 ml-2 grow"
                                onClick={noTeams}
                            />
                        </div>
                    }
                >
                    <div className="flex w-full flex-row flex-wrap">
                        {props.teams.map((t) => (
                            <div
                                key={t.id}
                                className="m-2 flex-none rounded bg-white p-2 shadow"
                            >
                                <Field
                                    type="checkbox"
                                    name="teams"
                                    value={t.id}
                                    className="checkboxinput align-middle"
                                />
                                <div
                                    className={classNames(
                                        "inline-block",
                                        "align-middle",
                                        "flex-none",
                                        "w-5",
                                        "h-5",
                                        "rounded",
                                        "m-1",
                                        "bg-" + t.color
                                    )}
                                >
                                    &nbsp;
                                </div>
                                <label className="mx-3 ml-0 align-middle">
                                    {t.name}
                                </label>
                            </div>
                        ))}
                    </div>
                </FormRow>
                <Button
                    disabled={props.submitting}
                    className="my-5 w-full bg-purple-500 hover:bg-purple-600"
                    type="submit"
                    label={
                        props.submitting
                            ? "Odesílám..."
                            : props.creatingNew
                            ? "Založit nové oznámení"
                            : "Uložit změny"
                    }
                />
            </Form>
        </div>
    );
}
