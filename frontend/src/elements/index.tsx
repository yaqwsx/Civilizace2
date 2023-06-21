import classNamesOriginal, { Argument } from "classnames";
import { ChangeEvent, useEffect, useRef } from "react";
import { ThreeDots } from "react-loader-spinner";
import ReactMarkdown from "react-markdown";
import { overrideTailwindClasses } from "tailwind-override";

import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { AxiosError, AxiosResponse } from "axios";
import _ from "lodash";
import React from "react";
import { useSelector } from "react-redux";
import { Navigate } from "react-router-dom";
import { RootState } from "../store";
import { EntityTag } from "./entities";

export const classNames = (...args: Argument[]) =>
    overrideTailwindClasses(classNamesOriginal(...args));

export function RequireAuth({ children }: JSX.ElementChildrenAttribute) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account ? <>{children}</> : <Navigate to="/login" />;
}

export function RequireOrg({ children }: JSX.ElementChildrenAttribute) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account?.user?.is_org ? (
        <>{children}</>
    ) : (
        <Navigate to="/forbidden" />
    );
}

export function RequireSuperOrg({ children }: JSX.ElementChildrenAttribute) {
    const auth = useSelector((state: RootState) => state.auth);
    return auth.account?.user?.is_org && auth.account?.user?.is_superuser ? (
        <>{children}</>
    ) : (
        <Navigate to="/forbidden" />
    );
}

export function InlineSpinner(props: { className?: string }) {
    return (
        <div
            className={classNames(
                "inline-block",
                "mx-auto",
                "text-gray-600",
                props.className
            )}
        >
            <ThreeDots height="100%" />
        </div>
    );
}

export function ComponentError(props: JSX.ElementChildrenAttribute) {
    return <div className="text-center text-gray-600">{props.children}</div>;
}

export function FormRow(props: {
    label: string | JSX.Element;
    className?: string;
    error?: any;
    extra?: JSX.Element;
    children: {};
}) {
    return (
        <div
            className={classNames(
                "md:flex",
                "md:items-center",
                "my-6",
                props.className
            )}
        >
            <div className="py-1 md:w-1/4">
                <label className="mb-1 block w-full pr-4 font-bold text-gray-500 md:mb-0 md:text-right">
                    {props.label}
                </label>
                <div className="mb-1 block w-full pr-4 text-red-600 md:mb-0 md:text-right">
                    {props.error || undefined}
                </div>
                <div className="mb-1 block w-full pr-4 md:mb-0 md:text-right">
                    {props.extra}
                </div>
            </div>
            <div className="field flex flex-wrap md:w-3/4">
                {props.children}
            </div>
        </div>
    );
}

type SpinboxInputType = {
    value?: number;
    onChange: (value: number) => void;
    className?: string;
    disabled?: boolean;
};
export function SpinboxInput(props: SpinboxInputType) {
    const incValue = (amount: number) => {
        let value = (props.value ?? 0) + amount;
        props.onChange(value);
    };

    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
        if (event.target.checkValidity()) {
            props.onChange(parseInt(event.target.value));
        }
    };

    const buttonClassName = classNames(
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
                disabled={props.disabled}
                onChange={handleChange}
                value={props.value ?? ""}
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

export function tryStringify(value: any, space?: number): string | undefined {
    if (typeof value === "string") {
        return value;
    }
    try {
        return JSON.stringify(value, null, space);
    } catch {}
    return;
}

function isAxiosError(error: any): error is AxiosError {
    return _.isObjectLike(error) && Boolean(error.isAxiosError);
}

function PrettyAxiosError(props: { errorResp: AxiosResponse }) {
    return (
        <div className="w-full">
            <h3>
                {props.errorResp.status} ({props.errorResp.statusText}):
            </h3>
            <code className="w-full overflow-hidden">
                <pre className="w-full overflow-hidden">
                    {tryStringify(props.errorResp.data, 2)}
                </pre>
            </code>
        </div>
    );
}

export function LoadingOrError(props: { error?: any; message: string }) {
    if (!props.error) {
        return <InlineSpinner />;
    }

    console.warn("Loading error:", props.message, {
        error: props.error,
    });
    return (
        <ComponentError>
            <p>{props.message}</p>
            {isAxiosError(props.error) && props.error.response ? (
                <PrettyAxiosError errorResp={props.error.response} />
            ) : (
                <>
                    <p>{String(props.error)}</p>
                    <p>
                        {tryStringify(props.error?.response?.data)?.substring(
                            0,
                            400
                        )}
                    </p>
                </>
            )}
        </ComponentError>
    );
}

export function Row(props: { children?: {}; className?: string }) {
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
    style?: React.CSSProperties;
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
        <button
            disabled={props.disabled}
            className={className}
            onClick={props.onClick}
            type={props.type ? props.type : "button"}
            style={props.style}
        >
            {props.label}
        </button>
    );
}

type TreeNode = TextNode | ElementNode;
interface TextNode {
    type: "text";
    value: string;
    children: TreeNode[];
}
interface ElementNode {
    type: "element";
    tagName: string;
    value: string[];
    children: TreeNode[];
}

export function EntityMdTag({ node }: { node: ElementNode }) {
    const [id, quantity = undefined] = node.value;
    return <EntityTag id={id} quantity={quantity} />;
}

function reconstructCiviMark(tree?: TreeNode) {
    const tagRe = /\[\[(.*?)\]\]/g;

    if (!tree?.children) return;
    for (let i = 0; i < tree.children.length; i++) {
        reconstructCiviMark(tree.children[i]);
    }
    const newChildren: TreeNode[] = [];
    for (let i = 0; i < tree.children.length; i++) {
        const node = tree.children[i];
        if (node.type == "text") {
            let isText = true;
            for (const x of node.value.split(tagRe)) {
                if (isText) {
                    newChildren.push({
                        type: "text",
                        value: x,
                        children: [],
                    });
                } else {
                    newChildren.push({
                        type: "element",
                        tagName: "EntityMdTag",
                        value: x.split("|").map((x) => x.trim()),
                        children: [],
                    });
                }
                isText = !isText;
            }
        } else {
            newChildren.push(node);
        }
    }
    tree.children = newChildren;
}

export function CiviMarkdown(props: { children: string; className?: string }) {
    const components: any = {
        EntityMdTag,
    };
    return (
        <ReactMarkdown
            rehypePlugins={[() => reconstructCiviMark]}
            components={components}
            {...props}
        />
    );
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
                className={classNames("h-8 w-8 md:h-4 md:w-4")}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                />
            </svg>
        </button>
    );
}

export function Dialog(props: { children: {}; onClose: () => void }) {
    useEffect(() => {
        document.documentElement.style.overflow = "hidden";
        return () => {
            document.documentElement.style.overflow = "scroll";
        };
    });

    return (
        <>
            <div className="fixed inset-0 z-30 h-screen w-screen bg-black opacity-50"></div>
            <div
                className="fixed inset-0 z-50 grid h-screen w-screen place-items-center py-1 px-1"
                onClick={props.onClose}
            >
                <div
                    className="container mx-auto flex max-h-full flex-col rounded bg-white p-2 pt-0"
                    style={{ overflowY: "scroll", overflowX: "clip" }}
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
                    <div className="w-full flex-1 px-3">{props.children}</div>
                </div>
            </div>
        </>
    );
}

export function useFocus<T extends HTMLElement>(): [
    React.RefObject<T>,
    () => void
] {
    const htmlElRef = useRef<T>(null);

    const setFocus = () => {
        htmlElRef?.current && htmlElRef.current.focus();
    };
    return [htmlElRef, setFocus];
}

export function Card(props: {
    color: string;
    label: string;
    children?: {};
    icon: IconDefinition;
}) {
    let bgColor = "bg-" + props.color;
    let textColor = "text-" + props.color;
    return (
        <div className="m-0 w-full px-0  py-2 md:w-1/2 md:px-2 xl:w-1/3">
            <div className="h-full rounded border bg-white p-2 shadow">
                <div className="flex h-full flex-row items-center">
                    <div className="h-full flex-shrink">
                        <div className={`rounded ${bgColor} p-3`}>
                            <FontAwesomeIcon
                                icon={props.icon}
                                className="fa fa-users fa-2x fa-fw fa-inverse"
                            />
                        </div>
                    </div>

                    <div className="h-full flex-1 px-4 text-right md:text-center">
                        <h5 className="mt-0 font-bold uppercase text-gray-500">
                            {props.label}
                        </h5>
                        {props.children}
                    </div>
                </div>
            </div>
        </div>
    );
}
