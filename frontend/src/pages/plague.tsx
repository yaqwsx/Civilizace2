// @ts-ignore
import { JsonEditor as Editor } from "jsoneditor-react";
import "jsoneditor-react/es/editor.min.css";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Button, Dialog, FormRow, LoadingOrError } from "../elements";
import { PerformAction } from "../elements/action";
import { fetcher } from "../utils/axios";
import { objectMap } from "../utils/functional";
import AceEditor from "react-ace";

import "ace-builds/webpack-resolver";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "ace-builds/src-noconflict/mode-javascript";
import { useHideMenu } from "./atoms";
import _ from "lodash";
import { Team } from "../types";
import { TeamSelector } from "../elements/team";

export function PlagueMenu() {
    return null;
}

export function Plague() {
    useHideMenu();
    const [team, setTeam] = useState<Team | undefined>(undefined);
    const [action, setAction] = useState<string | undefined>(undefined);

    return (
        <>
            <h1>Správa moru</h1>
            <FormRow label="Vyber tým">
                <TeamSelector active={team} onChange={setTeam} />
            </FormRow>
            {team && (
                <FormRow label="Vyberte akci:">
                    <Button
                        label="Začít mor"
                        className="m-2 flex-1 bg-orange-600 hover:bg-orange-700"
                        onClick={() => setAction("ActionPlagueStart")}
                    />
                    <Button
                        label="Ukončit mor"
                        className="m-2 flex-1 bg-green-600 hover:bg-green-700"
                        onClick={() => setAction("ActionPlagueFinish")}
                    />
                </FormRow>
            )}
            {action && (
                <Dialog onClose={() => setAction(undefined)}>
                    <PerformAction
                        actionName="Manipulace s morem"
                        actionId={action}
                        actionArgs={{ team: team?.id }}
                        onFinish={() => setAction(undefined)}
                        onBack={() => setAction(undefined)}
                    />
                </Dialog>
            )}
        </>
    );
}
