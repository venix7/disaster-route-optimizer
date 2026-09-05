import { useMapEvents } from "react-leaflet";


function LocationSelector({
    selectionMode,
    onLocationSelect
}) {

    useMapEvents({

        click(event) {

            const {
                lat,
                lng
            } = event.latlng;

            if (!selectionMode) {
                return;
            }

            onLocationSelect(
                lat,
                lng,
                selectionMode
            );

        }

    });

    return null;

}


export default LocationSelector;