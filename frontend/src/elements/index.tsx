import { ChangeEvent, useEffect, useState } from "react";
import useSWR from "swr";
import { Team, UserResponse } from "../types";
import { fetcher } from "../utils/axios";
import { ThreeDots } from "react-loader-spinner";
import classNames from "classnames";
import ReactMarkdown from "react-markdown";
import { JsxElement } from "typescript";

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
    error?: any;
    children: any;
    extra?: any;
};
export function FormRow(props: FormRowProps) {
    let className = "md:flex md:items-center mb-6";
    if (props.className) className += " " + props.className;
    return (
        <div className={className}>
            <div className="py-1 md:w-1/4">
                <label className="mb-1 block pr-4 font-bold text-gray-500 md:mb-0 md:text-right w-full">
                    {props.label}
                </label>
                <div className="mb-1 block w-full text-red-600 md:mb-0 md:text-right">
                    {props.error ? props.error : null}
                </div>
                <div className="mb-1 block pr-4 md:mb-0 md:text-right w-full">
                    {props.extra ? props.extra : null}
                </div>
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
    if (props.error) {
        return (
            <ComponentError>
                <p>{props.message}</p>
                <p>{props.error.toString()}</p>
            </ComponentError>
        );
    }
    if (props.loading) {
        return <InlineSpinner />;
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
    type?: "button" | "submit" | "reset" | undefined;
    disabled?: boolean;
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
        "bg-purple-500",
        "hover:bg-purple-600",
        "disabled:bg-gray-500",
        props.className
    );
    return (
        <button disabled={props.disabled} className={className} onClick={props.onClick} type={props.type}>
            {props.label}
        </button>
    );
}

export function CiviMarkdown(props: any) {
    return <ReactMarkdown {...props} />;
}

export function CloseButton(props: {
    onClick: () => void;
    className?: string;
}) {
    return (
        <button
            type="button"
            onClick={props.onClick}
            className={classNames(
                "inline-flex",
                "items-center",
                "justify-center",
                "rounded-md",
                "bg-white",
                "p-2",
                "text-gray-400",
                "hover:bg-gray-100",
                "hover:text-gray-500",
                "focus:outline-none",
                "focus:ring-2",
                "focus:ring-inset",
                "focus:ring-indigo-500",
                props.className
            )}
        >
            <span className="sr-only">Close</span>
            <svg
                className="h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                />
            </svg>
        </button>
    );
}

function stopPropagation(e: any) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}

export function Dialog(props: { children: any; onClose: () => void }) {
    useEffect(() => {
        document.documentElement.style.overflow = "hidden";
        return () => {
            document.documentElement.style.overflow = "scroll";
        };
        // This doesn't work:
        // document.body.addEventListener("scroll", stopPropagation);
        // document.body.addEventListener("mousewheel", stopPropagation);
        // document.body.addEventListener("touchmove", stopPropagation);
        // return () => {
        //     document.body.removeEventListener("scroll", stopPropagation);
        //     document.body.removeEventListener("mousewheel", stopPropagation);
        //     document.body.removeEventListener("touchmove", stopPropagation);
        // }
    });

    return (
        <>
            <div className="fixed inset-0 z-30 h-screen w-screen bg-black opacity-50"></div>
            <div
                className="fixed inset-0 z-50 h-screen w-screen py-5 px-2 grid place-items-center"
                onClick={props.onClose}
            >
                <div
                    className="container mx-auto flex max-h-full flex-col rounded bg-white p-5"
                    onClick={(e) => {
                        e.stopPropagation();
                    }}
                >
                    <div className="flex w-full flex-none flex-row-reverse">
                        <CloseButton
                            onClick={props.onClose}
                            className="flex-none"
                        />
                    </div>
                    <hr className="my-2 h-1 rounded bg-gray-300 shadow" />
                    <div className="w-full flex-1 overflow-y-auto">
                        {props.children}
                    </div>
                </div>
            </div>
        </>
    );
}
