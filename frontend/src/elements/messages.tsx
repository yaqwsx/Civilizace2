import classNames from "classnames";

type MessageProps = {
    children: any;
    className?: string;
};

export function ErrorMessage(props: MessageProps) {
    let className = classNames(
        "relative", "my-6", "rounded", "border", "border-red-400", "bg-red-100",
        "px-4", "py-3", "text-red-700"
    );

    if (props.className) {
        className += " " + props.className;
    }
    return <div className={className}>{props.children}</div>;
}
