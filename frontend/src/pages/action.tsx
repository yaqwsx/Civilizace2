import _ from "lodash";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import { LoadingOrError } from "../elements";
import {
    ActionDicePhase,
    ActionFinishPhase,
    useUnfinishedActions,
} from "../elements/action";
import { ErrorMessage, SuccessMessage } from "../elements/messages";
import { ActionResponse } from "../types";

export function FinishAction() {
    const navigate = useNavigate();
    const { actionId } = useParams();
    const { actions, error, mutate } = useUnfinishedActions();
    const [response, setResponse] = useState<ActionResponse>();

    if (!actionId)
        return <ErrorMessage>Nastala neočekávaná chyba</ErrorMessage>;
    if (!actions) {
        return <LoadingOrError error={error} message="Něco se nepovedlo" />;
    }

    const action = actions.find((x) => x.id === parseInt(actionId));
    if (!action)
        return (
            <SuccessMessage>
                Akce už byla dokončena. Můžete pokračovat.
            </SuccessMessage>
        );

    const actionName = `Dokončení akce ${action.id}: ${action?.description}`;

    return (
        <>
            <h1>
                Máte nedokončenou akci {actionId}, je třeba ji dokončit než
                můžete zadávat další akce.
            </h1>
            {_.isNil(response) ? (
                <ActionDicePhase
                    actionNumber={action.id}
                    message={""}
                    changePhase={(p, d) => {
                        console.assert(
                            !_.isNil(d),
                            "Empty ActionResponse in",
                            p
                        );
                        setResponse(d);
                    }}
                    actionName={actionName}
                />
            ) : (
                <ActionFinishPhase
                    response={response}
                    actionName={actionName}
                    onFinish={() => {
                        toast.success("Nedokončená akce dokončena!");
                        navigate(-1);
                        mutate();
                    }}
                />
            )}
        </>
    );
}
