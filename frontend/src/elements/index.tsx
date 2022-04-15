import { ChangeEvent, useState } from 'react';
import useSWR from 'swr';
import { Team, UserResponse } from "../types"
import { fetcher } from "../utils/axios"
import { ThreeDots } from "react-loader-spinner"
import classNames from "classnames";

// Avoid purging team background colors
let teamColorPlaceholder = ["bg-gray-600", "bg-red-600", "bg-orange-500",
    "bg-yellow-500", "bg-green-600", "bg-blue-600", "bg-purple-500",
    "bg-pink-600"];

type InlineSpinnerProps = {
    className?: string;
};
export function InlineSpinner(props: InlineSpinnerProps) {
    let className = classNames("inline-block", "mx-auto", "text-gray-600");
    if (props.className)
        className += " " + props.className;
    return <div className={className}>
        <ThreeDots height="100%" />
    </div>
}

type ComponentErrorProps = {
    children: any
}
export function ComponentError(props: ComponentErrorProps) {
    return <div className="text-center text-gray-600">
        {props.children}
    </div>
}

type FormRowProps = {
    label: string;
    className?: string;
    children: any;
}
export function FormRow(props: FormRowProps) {
    let className = "md:flex md:items-center mb-6";
    if (props.className)
        className += " " + props.className;
    return <div className={className}>
        <div className="md:w-1/4 py-2">
            <label className="block text-gray-500 font-bold md:text-right mb-1 md:mb-0 pr-4">
                {props.label}
            </label>
        </div>
        <div className="md:w-3/4 flex flex-wrap field">
            {props.children}
        </div>
    </div>
}

type SpinboxInputType = {
    value: number;
    onChange: (value: number) => void;
    className?: string;
}
export function SpinboxInput(props: SpinboxInputType) {

    const incValue = (amount: number) => {
        let value = props.value + amount;
        props.onChange(value);
    };

    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
        props.onChange(parseInt(event.target.value));
    }

    let buttonClassName = classNames("inline-block", "shadow", "text-center",
        "bg-purple-500", "hover:bg-purple-400", "focus:shadow-outline",
        "focus:outline-none", "text-white", "font-bold", "py-2", "px-4",
        "rounded", "flex-none", "mx-1", "text-xs");

    return (
        <div className={classNames("w-full flex flex-wrap", props.className)}>
            <button className={buttonClassName}
                onClick={() => incValue(-5)}>
                ↓↓
            </button>
            <button className={buttonClassName}
                onClick={() => incValue(-1)}>
                ↓
            </button>
            <input type="number"
                   onChange={handleChange}
                   value={String(props.value)}
                   className="numberinput flex-1 mx-3"/>
            <button className={buttonClassName}
                onClick={() => incValue(1)}>
                ↑
            </button>
            <button className={buttonClassName}
                onClick={() => incValue(5)}>
                ↑↑
            </button>
        </div>
    )
}
