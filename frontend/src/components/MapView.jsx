import { MapContainer, TileLayer, Polyline, Marker, Circle, Tooltip } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import ShelterMarkers from "./ShelterMarkers";
import LocationSelector from "./LocationSelector";

const recommendedShelterIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [0, -30],
  shadowSize: [41, 41],
});

const defaultMarkerIcon = new L.Icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [0, -30],
  shadowSize: [41, 41],
});

function MapView({
  route,
  shelters,
  floodData,
  recommendedShelter,
  userLocation,
  destinationLocation,
  selectionMode,
  onLocationSelect,
}) {
  const routePositions =
    route?.coordinates?.map((coordinate) => [coordinate.latitude, coordinate.longitude]) || [];

  const validUserLocation =
    userLocation && !isNaN(userLocation.latitude) && !isNaN(userLocation.longitude);

  const validDestinationLocation =
    destinationLocation &&
    !isNaN(destinationLocation.latitude) &&
    !isNaN(destinationLocation.longitude);

  const validRecommendedShelter =
    recommendedShelter &&
    !isNaN(recommendedShelter.latitude) &&
    !isNaN(recommendedShelter.longitude);

  return (
    <div className="map-container">
      <MapContainer
        center={[40.7306, -73.995]}
        zoom={14}
        scrollWheelZoom={false}
        style={{ height: "600px", width: "100%" }}
      >
        <TileLayer
          attribution="© OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Handles map clicks */}
        <LocationSelector selectionMode={selectionMode} onLocationSelect={onLocationSelect} />

        {/* User selected starting location */}
        {validUserLocation && (
          <Marker position={[userLocation.latitude, userLocation.longitude]} icon={defaultMarkerIcon}>
            <Tooltip permanent direction="top" offset={[0, -30]}>
              YOU
            </Tooltip>
          </Marker>
        )}

        {/* User selected destination */}
        {validDestinationLocation && (
          <Marker
            position={[destinationLocation.latitude, destinationLocation.longitude]}
            icon={defaultMarkerIcon}
          >
            <Tooltip permanent direction="top" offset={[0, -30]}>
              DESTINATION
            </Tooltip>
          </Marker>
        )}

        {/* Flood visualization */}
        {floodData && (
          <>
            {/* Affected area */}
            <Circle
              center={[floodData.latitude, floodData.longitude]}
              radius={floodData.affectedRadius}
              pathOptions={{ fillOpacity: 0.15 }}
            />

            {/* Severe flood area */}
            <Circle
              center={[floodData.latitude, floodData.longitude]}
              radius={floodData.severeRadius}
              pathOptions={{ fillOpacity: 0.35 }}
            />

            {/* Flood center marker */}
            <Marker position={[floodData.latitude, floodData.longitude]} icon={defaultMarkerIcon}>
              <Tooltip permanent direction="top" offset={[0, -30]}>
                FLOOD CENTER
              </Tooltip>
            </Marker>
          </>
        )}

        {/* All emergency shelters */}
        <ShelterMarkers shelters={shelters} />

        {/* Recommended shelter marker */}
        {validRecommendedShelter && (
          <Marker
            position={[recommendedShelter.latitude, recommendedShelter.longitude]}
            icon={recommendedShelterIcon}
            zIndexOffset={1000}
          >
            <Tooltip permanent direction="top" offset={[0, -30]}>
              RECOMMENDED SHELTER
            </Tooltip>
          </Marker>
        )}

        {/* Calculated evacuation route */}
        {routePositions.length > 0 && <Polyline positions={routePositions} weight={5} />}
      </MapContainer>
    </div>
  );
}

export default MapView;