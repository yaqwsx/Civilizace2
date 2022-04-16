import { ChangeEvent, useState } from "react";
import useSWR from "swr";
import { Team, UserResponse } from "../types";
import { fetcher } from "../utils/axios";
import { ThreeDots } from "react-loader-spinner";
import classNames from "classnames";

// Avoid purging team background colors
let teamColorPlaceholder = [
    "bg-gray-600",
    "bg-red-600",
    "bg-orange-500",
    "bg-yellow-500",
    "bg-green-600",
    "bg-blue-600",
    "bg-purple-500",
    "bg-pink-600",
];

type InlineSpinnerProps = {
    className?: string;
};
export function InlineSpinner(props: InlineSpinnerProps) {
    let className = classNames("inline-block", "mx-auto", "text-gray-600");
    if (props.className) className += " " + props.className;
    return (
        <div className={className}>
            <ThreeDots height="100%" />
        </div>
    );
}

type ComponentErrorProps = {
    children: any;
};
export function ComponentError(props: ComponentErrorProps) {
    return <div className="text-center text-gray-600">{props.children}</div>;
}

type FormRowProps = {
    label: string;
    className?: string;
    children: any;
};
export function FormRow(props: FormRowProps) {
    let className = "md:flex md:items-center mb-6";
    if (props.className) className += " " + props.className;
    return (
        <div className={className}>
            <div className="py-2 md:w-1/4">
                <label className="mb-1 block pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                    {props.label}
                </label>
            </div>
            <div className="field flex flex-wrap md:w-3/4">
                {props.children}
            </div>
        </div>
    );
}

type SpinboxInputType = {
    value: number;
    onChange: (value: number) => void;
    className?: string;
};
export function SpinboxInput(props: SpinboxInputType) {
    const incValue = (amount: number) => {
        let value = props.value + amount;
        props.onChange(value);
    };

    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
        props.onChange(parseInt(event.target.value));
    };

    let buttonClassName = classNames(
        "inline-block",
        "shadow",
        "text-center",
        "bg-purple-500",
        "hover:bg-purple-400",
        "focus:shadow-outline",
        "focus:outline-none",
        "text-white",
        "font-bold",
        "py-2",
        "px-4",
        "rounded",
        "flex-none",
        "mx-1",
        "text-xs"
    );

    return (
        <div className={classNames("flex w-full flex-wrap", props.className)}>
            <button className={buttonClassName} onClick={() => incValue(-5)}>
                ↓↓
            </button>
            <button className={buttonClassName} onClick={() => incValue(-1)}>
                ↓
            </button>
            <input
                type="number"
                onChange={handleChange}
                value={String(props.value)}
                className="numberinput mx-3 flex-1"
            />
            <button className={buttonClassName} onClick={() => incValue(1)}>
                ↑
            </button>
            <button className={buttonClassName} onClick={() => incValue(5)}>
                ↑↑
            </button>
        </div>
    );
}

export function LoadingOrError(props: {
    loading: boolean;
    error?: any;
    message: string;
}) {
    if (props.loading) {
        return <InlineSpinner />;
    }
    if (props.error) {
        return (
            <ComponentError>
                <p>{props.message}</p>
                <p>{props.error.toString()}</p>
            </ComponentError>
        );
    }
    return null;
}

export function Row(props: { children: any; className?: string }) {
    return (
        <div className={classNames("w-full", props.className)}>
            {props.children}
        </div>
    );
}

export function Button(props: {
    label: string;
    onClick?: () => void;
    className?: string;
}) {
    const className = classNames(
        "rounded",
        "shadow",
        "text-white",
        "font-bold",
        "py-2",
        "px-4",
        "mx-2",
        "rounded",
        "focus:shadow-outline",
        "focus:outline-none",
        props.className
    );
    return (
        <button className={className} onClick={props.onClick}>
            {props.label}
        </button>
    );
}
