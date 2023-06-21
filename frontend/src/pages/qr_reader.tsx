import BarcodeScannerComponent from "react-qr-barcode-scanner";
import { useNavigate } from "react-router-dom";
import { getNavigatePage } from "../elements/scanner";

export function QrReader() {
    const navigate = useNavigate();

    return (
        <div className="my-10 flex justify-center">
            <BarcodeScannerComponent
                width={500}
                height={500}
                onUpdate={(err: any, result) => {
                    if (result) {
                        console.log("QR Reader:", result.getText(), result);
                        const { page, args } = getNavigatePage(
                            result.getText().split(" ")
                        );
                        console.log({ page, args });

                        if (page) {
                            console.log(
                                `Navigating to ${page}#${args.join("&")}`
                            );
                            navigate("../" + page);
                            window.location.hash = `#${args.join("&")}`;
                        }
                    }
                }}
            />
        </div>
    );
}
