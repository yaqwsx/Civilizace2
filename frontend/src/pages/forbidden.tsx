import { useHideMenu } from "./atoms";

export function Forbidden() {
    useHideMenu();
    return <p>This page is forbidden</p>;
}
