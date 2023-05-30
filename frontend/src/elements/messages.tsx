import { classNames } from ".";

type MessageProps = {
    children: any;
    className?: string;
};

export function ErrorMessage(props: MessageProps) {
    let className = classNames(
        "relative",
        "my-6",
        "rounded",
        "border",
        "border-red-400",
        "bg-red-100",
        "px-4",
        "py-3",
        "text-red-700"
    );

    if (props.className) {
        className += " " + props.className;
    }
    return <div className={className}>{props.children}</div>;
}

export function SuccessMessage(props: MessageProps) {
    let className = classNames(
        "relative",
        "my-6",
        "rounded",
        "border",
        "border-green-400",
        "bg-green-100",
        "px-4",
        "py-3",
        "text-green-700"
    );

    if (props.className) {
        className += " " + props.className;
    }
    return <div className={className}>{props.children}</div>;
}

export function WarningMessage(props: MessageProps) {
    let className = classNames(
        "relative",
        "my-6",
        "rounded",
        "border",
        "border-orange-400",
        "bg-orange-100",
        "px-4",
        "py-3",
        "text-orange-700"
    );

    if (props.className) {
        className += " " + props.className;
    }
    return <div className={className}>{props.children}</div>;
}

export function NeutralMessage(props: MessageProps) {
    let className = classNames(
        "relative",
        "my-6",
        "rounded",
        "border",
        "border-blue-400",
        "bg-blue-100",
        "px-4",
        "py-3",
        "text-blue-700"
    );

    if (props.className) {
        className += " " + props.className;
    }
    return <div className={className}>{props.children}</div>;
}
