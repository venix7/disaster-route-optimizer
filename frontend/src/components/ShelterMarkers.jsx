import {
    CircleMarker,
    Popup
} from "react-leaflet";


function ShelterMarkers({ shelters }) {

    if (!shelters || shelters.length === 0) {
        return null;
    }

    return (
        <>
            {shelters.map((shelter) => (

                <CircleMarker
                    key={shelter.id}
                    center={[
                        shelter.latitude,
                        shelter.longitude
                    ]}
                    radius={8}
                    pathOptions={{
                        color: "red",
                        fillColor: "red",
                        fillOpacity: 0.8
                    }}
                >

                    <Popup>
                        <div>

                            <h3>
                                {shelter.name}
                            </h3>

                            <p>
                                Capacity: {
                                    shelter.capacity
                                }
                            </p>

                            <p>
                                Status: {
                                    shelter.status
                                }
                            </p>

                        </div>
                    </Popup>

                </CircleMarker>

            ))}
        </>
    );
}


export default ShelterMarkers;