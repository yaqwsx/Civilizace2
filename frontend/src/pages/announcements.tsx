import classNames from "classnames";
import { ErrorMessage, Field, Form, Formik } from "formik";
import { useState } from "react";
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
import { useTeams } from "../elements/team";
import { Announcement, AnnouncementType, Team } from "../types";
import { fetcher } from "../utils/axios";
import { combineErrors } from "../utils/error";
import DateTime from "react-datetime";
import "react-datetime/css/react-datetime.css";

export function AnnouncementsMenu() {
    return null;
}

export function Announcements() {
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
    const { data: announcements, error } = useSWR<Announcement[]>(
        "game/announcement",
        fetcher
    );
    const { teams, loading: teamLoading, error: teamError } = useTeams();

    if (!announcements || error || !teams || teamError)
        return (
            <LoadingOrError
                loading={(!announcements && !error) || teamLoading}
                error={combineErrors([error, teamError])}
                message="Nastala chyba"
            />
        );
    return (
        <>
            <h2>Správa vývěsky</h2>
            <Link to="new">
                <Button label="Nové oznámení" className="mx-0 my-2 w-full" />
            </Link>
            {announcements.map((a) => (
                <AnnouncementItem announcement={a} teams={teams} />
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
    }
}

function AnnouncementItem(props: {
    announcement: Announcement;
    teams: Team[];
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
                <FormRow label="Autor:" className="mb-0">
                    <p>{props.announcement.author}</p>
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
                <Dialog onClose={() => setdDialog(false)}>
                    <h2>Skutečně smazat oznámení {props.announcement.id}?</h2>
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

function AnnouncementEdit() {
    const { announcementId } = useParams();
    const { teams, error: teamError, loading: teamLoading } = useTeams();
    const { data: announcement, error: announcementError } =
        useSWR<Announcement>(
            () =>
                announcementId ? `game/announcement/${announcementId}` : null,
            (url) =>
                fetcher(url).then((a) => {
                    console.log(a);
                    a.appearDatetime = new Date(a.appearDatetime);
                    console.log(a);
                    return a;
                })
        );

    if ((announcementId && !announcement) || teamError || teamLoading || !teams)
        return (
            <LoadingOrError
                loading={teamLoading || (!announcement && !announcementId)}
                error={combineErrors([announcementError, teamError])}
                message="Nastala chyba"
            />
        );

    const handleSubmit = (data: Announcement) => {
        console.log(data);
    };

    const initialValues: Announcement = {
        id: -1,
        author: "",
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
            <Formik<Announcement>
                initialValues={announcement ? announcement : initialValues}
                onSubmit={handleSubmit}
            >
                {(props) => (
                    <AnnouncementEditForm
                        values={props.values}
                        setFieldValue={props.setFieldValue}
                        teams={teams}
                    />
                )}
            </Formik>
        </>
    );
}

function AnnouncementEditForm(props: {
    values: Announcement;
    setFieldValue: (field: string, value: any, validate: boolean) => void;
    teams: Team[];
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
    return (
        <div className="w-full">
            <Form {...props}>
                <FormRow
                    label="Viditelné od:"
                    error={<ErrorMessage name="appearDatetime" />}
                >
                    <DateTime
                        className="w-full"
                        dateFormat="D. M."
                        timeFormat="H:mm"
                        value={props.values.appearDatetime}
                        onChange={(date: any) =>
                            props.setFieldValue("appearDatetime", date, true)
                        }
                    />
                </FormRow>
                <FormRow label="Typ:" error={<ErrorMessage name="type" />}>
                    <select
                        className="select"
                        value={props.values.type}
                        onChange={(e) =>
                            props.setFieldValue("type", e.target.value, true)
                        }
                    >
                        {Object.values(AnnouncementType).map((t) => (
                            <option key={t} value={t}>
                                {translateAnnouncementType(
                                    t as AnnouncementType
                                )}
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
                <Button
                    className="my-5 w-full bg-purple-500 hover:bg-purple-600"
                    type="submit"
                    label={
                        props.values.id != -1
                            ? "Uložit změny"
                            : "Založit nové oznámení"
                    }
                />
            </Form>
        </div>
    );
}
