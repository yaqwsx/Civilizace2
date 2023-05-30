import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import { LoadingOrError } from "../elements";
import {
    ActionDicePhase,
    ActionFinishPhase,
    ActionPhase,
    useUnfinishedActions,
} from "../elements/action";
import { ErrorMessage, SuccessMessage } from "../elements/messages";

export function FinishAction() {
    const navigate = useNavigate();
    const { actionId } = useParams();
    const { actions, error, mutate } = useUnfinishedActions();
    const [finished, setFinished] = useState(false);
    const [response, setResponse] = useState<any>(undefined);

    if (!actionId)
        return <ErrorMessage>Nastala neočekávaná chyba</ErrorMessage>;
    if (!actions) {
        return (
            <LoadingOrError
                loading={!actions && !error}
                error={error}
                message="Něco se nepovedlo"
            />
        );
    }

    let action = actions?.find((x) => x.id === parseInt(actionId));
    if (!action)
        return (
            <SuccessMessage>
                Akce už byla dokončena. Můžete pokračovat.
            </SuccessMessage>
        );

    let actionName = `Dokončení akce ${action.id}: ${action?.description}`;

    return (
        <>
            <h1>
                Máte nedokončenou akci {actionId}, je třeba ji dokončit než
                můžete zadávat další akce.
            </h1>
            {!finished ? (
                <ActionDicePhase
                    actionNumber={action.id}
                    message={""}
                    changePhase={(p, d) => {
                        setResponse(d);
                        setFinished(true);
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
