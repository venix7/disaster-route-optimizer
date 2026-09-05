import axios from "axios";


const api = axios.create({
    baseURL: "http://127.0.0.1:8000"
});


export const getShelters = async () => {

    const response = await api.get(
        "/shelters"
    );

    return response.data.shelters;
};


export const findRoute = async (
    startLatitude,
    startLongitude,
    destinationLatitude,
    destinationLongitude
) => {

    const response = await api.post(
        "/route",
        {
            start_latitude: startLatitude,
            start_longitude: startLongitude,
            destination_latitude: destinationLatitude,
            destination_longitude: destinationLongitude
        }
    );

    return response.data;
};


export const findBestShelter = async (
    startLatitude,
    startLongitude
) => {

    const response = await api.post(
        "/evacuation/best-shelter",
        {
            start_latitude: startLatitude,
            start_longitude: startLongitude
        }
    );

    return response.data;
};

export const simulateFlood = async (
    centerLatitude,
    centerLongitude,
    affectedRadius,
    severeRadius
) => {

    const response = await api.post(
        "/disaster/flood",
        {
            center_latitude: centerLatitude,
            center_longitude: centerLongitude,
            affected_radius: affectedRadius,
            severe_radius: severeRadius
        }
    );

    return response.data;
};


export const resetDisaster = async () => {

    const response = await api.post(
        "/disaster/reset"
    );

    return response.data;
};