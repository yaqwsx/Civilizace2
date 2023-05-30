import { ToastContainer, ToastClassName } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const contextClass: Record<string, string> = {
    success: "bg-green-100 border border-green-400 text-green-700",
    error: "bg-red-100 border border-red-400 text-red-700",
    info: "bg-gray-600",
    warning: "bg-orange-400",
    default: "bg-indigo-600",
    dark: "bg-white-600 font-gray-300",
};

let toastClassName: ToastClassName = (props) => {
    return (
        contextClass[props?.type || "default"] +
        " relative flex p-1 min-h-10 rounded-md justify-between overflow-hidden cursor-pointer"
    );
};

export function ToastProvider() {
    return (
        <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            toastClassName={toastClassName}
            bodyClassName={() => "text-sm font-white font-med block p-3"}
        />
    );
}
