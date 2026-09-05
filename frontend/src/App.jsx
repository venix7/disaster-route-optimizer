import { useEffect, useState } from "react";
import "./App.css";
import MapView from "./components/MapView";
import {
  getShelters,
  findRoute,
  findBestShelter,
  simulateFlood,
  resetDisaster,
} from "./services/api";

function App() {
  const [shelters, setShelters] = useState([]);
  const [route, setRoute] = useState(null);
  const [recommendedShelter, setRecommendedShelter] = useState(null);

  // Selected route locations
  const [startLatitude, setStartLatitude] = useState("");
  const [startLongitude, setStartLongitude] = useState("");
  const [destinationLatitude, setDestinationLatitude] = useState("");
  const [destinationLongitude, setDestinationLongitude] = useState("");

  // Selected flood location
  const [floodLatitude, setFloodLatitude] = useState("");
  const [floodLongitude, setFloodLongitude] = useState("");
  const [affectedRadius, setAffectedRadius] = useState("500");
  const [severeRadius, setSevereRadius] = useState("200");

  const [disasterActive, setDisasterActive] = useState(false);
  const [floodData, setFloodData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectionMode, setSelectionMode] = useState(null);

  useEffect(() => {
    const loadShelters = async () => {
      try {
        const data = await getShelters();
        setShelters(data.shelters || []);
      } catch (error) {
        console.error("Failed to load shelters:", error);
      }
    };

    loadShelters();
  }, []);

  const handleFindRoute = async () => {
    if (
      !startLatitude ||
      !startLongitude ||
      !destinationLatitude ||
      !destinationLongitude
    ) {
      setError(
        "Please select a start location and destination on the map."
      );
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setRecommendedShelter(null);

      const data = await findRoute(
        parseFloat(startLatitude),
        parseFloat(startLongitude),
        parseFloat(destinationLatitude),
        parseFloat(destinationLongitude)
      );

      setRoute(data);

    } catch (error) {
      console.error(error);

      if (error.response?.status === 404) {
        setError(
          "No evacuation route is available. The selected location may be isolated by blocked flood roads."
        );
      } else {
        setError("Failed to calculate evacuation route.");
      }

    } finally {
      setLoading(false);
    }
  };

  const handleFindBestShelter = async () => {
    if (!startLatitude || !startLongitude) {
      setError("Please select a starting location.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setDestinationLatitude("");
      setDestinationLongitude("");

      const data = await findBestShelter(parseFloat(startLatitude), parseFloat(startLongitude));
      const bestResult = data.recommended_shelter;

      if (!bestResult || !bestResult.route || !bestResult.shelter) {
        throw new Error("No recommended shelter or route returned.");
      }

      setRoute(bestResult.route);
      setRecommendedShelter(bestResult.shelter);
    } catch (error) {
      console.error(error);

      if (error.response?.status === 404) {
        setError(
          "No reachable evacuation shelter was found. Flood conditions may have isolated the selected location."
        );
      } else {
        setError("Failed to find the best evacuation shelter.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateFlood = async () => {
    if (!floodLatitude || !floodLongitude || !affectedRadius || !severeRadius) {
      setError("Please select a flood center and enter flood parameters.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await simulateFlood(
        parseFloat(floodLatitude),
        parseFloat(floodLongitude),
        parseFloat(affectedRadius),
        parseFloat(severeRadius)
      );

      setFloodData({
        latitude: parseFloat(floodLatitude),
        longitude: parseFloat(floodLongitude),
        affectedRadius: parseFloat(affectedRadius),
        severeRadius: parseFloat(severeRadius),
      });

      setDisasterActive(true);
    } catch (error) {
      console.error(error);
      setError("Failed to simulate flood.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetDisaster = async () => {
    try {
      setLoading(true);
      setError(null);

      await resetDisaster();

      setDisasterActive(false);
      setFloodData(null);
      setRoute(null);
      setRecommendedShelter(null);
      setFloodLatitude("");
      setFloodLongitude("");
    } catch (error) {
      console.error(error);
      setError("Failed to reset disaster.");
    } finally {
      setLoading(false);
    }
  };

  const handleLocationSelect = (latitude, longitude, mode) => {
    if (mode === "start") {
      setStartLatitude(latitude.toString());
      setStartLongitude(longitude.toString());
      setSelectionMode("destination");
    } else if (mode === "destination") {
      setDestinationLatitude(latitude.toString());
      setDestinationLongitude(longitude.toString());
      setSelectionMode(null);
    } else if (mode === "flood") {
      setFloodLatitude(latitude.toString());
      setFloodLongitude(longitude.toString());
      setSelectionMode(null);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div>
          <h1>
            Disaster Evacuation
            <span> Route Optimizer</span>
          </h1>
          <p>Intelligent routing and emergency response planning</p>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          SYSTEM ONLINE
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="dashboard">
        {/* Control Panels */}
        <section className="controls-grid">
          {/* Route Planning */}
          <div className="control-panel route-panel">
            <div className="panel-heading">
              <div className="panel-icon">🧭</div>
              <div>
                <h2>Route Planning</h2>
                <p>Select locations and calculate the safest evacuation route.</p>
              </div>
            </div>

            <button
              className="primary-button"
              onClick={() => {
                setRoute(null);
                setRecommendedShelter(null);
                setDestinationLatitude("");
                setDestinationLongitude("");
                setSelectionMode("start");
              }}
              disabled={loading}
            >
              📍 Select Start Location
            </button>

            {selectionMode === "start" && (
              <div className="instruction-message">
                Click anywhere on the map to select your location.
              </div>
            )}

            {selectionMode === "destination" && (
              <div className="instruction-message">Now select your destination on the map.</div>
            )}

            <div className="button-row">
              <button className="secondary-button" onClick={handleFindRoute} disabled={loading}>
                Find Route
              </button>

              <button
                className="secondary-button"
                onClick={handleFindBestShelter}
                disabled={loading}
              >
                Find Best Shelter
              </button>
            </div>
          </div>

          {/* Flood Simulation */}
          <div className="control-panel flood-panel">
            <div className="panel-heading">
              <div className="panel-icon">⚠️</div>
              <div>
                <h2>Flood Simulation</h2>
                <p>Simulate affected zones and update route safety.</p>
              </div>
            </div>

            <div className="input-grid">
              <div className="input-group">
                <label>Affected Radius</label>
                <input
                  type="number"
                  value={affectedRadius}
                  onChange={(event) => setAffectedRadius(event.target.value)}
                />
                <span>meters</span>
              </div>

              <div className="input-group">
                <label>Severe Radius</label>
                <input
                  type="number"
                  value={severeRadius}
                  onChange={(event) => setSevereRadius(event.target.value)}
                />
                <span>meters</span>
              </div>
            </div>

            <button
              className="primary-button flood-button"
              onClick={() => {
                setFloodData(null);
                setSelectionMode("flood");
              }}
              disabled={loading}
            >
              🌊 Select Flood Center
            </button>

            {selectionMode === "flood" && (
              <div className="instruction-message">
                Click on the map to select the flood center.
              </div>
            )}

            <div className="button-row">
              <button
                className="secondary-button simulate-button"
                onClick={handleSimulateFlood}
                disabled={loading}
              >
                Simulate Flood
              </button>

              {disasterActive && (
                <button className="reset-button" onClick={handleResetDisaster} disabled={loading}>
                  Reset
                </button>
              )}
            </div>

            {disasterActive && <div className="disaster-status">⚠ Flood simulation active</div>}
          </div>
        </section>

        {/* Status Messages */}
        {loading && (
          <div className="loading-message">
            <div className="loader"></div>
            Processing request...
          </div>
        )}

        {error && <div className="error-message">⚠ {error}</div>}

        {/* Map */}
        <section className="map-section">
          <div className="section-header">
            <div>
              <h2>Interactive Evacuation Map</h2>
              <p>Select locations directly on the map</p>
            </div>

            <div className="map-legend">
              <span>🔵 Start</span>
              <span>🔴 Shelter</span>
              <span>🌊 Flood Zone</span>
            </div>
          </div>

          <MapView
            route={route}
            shelters={shelters}
            floodData={floodData}
            recommendedShelter={recommendedShelter}
            userLocation={
              startLatitude && startLongitude
                ? { latitude: parseFloat(startLatitude), longitude: parseFloat(startLongitude) }
                : null
            }
            destinationLocation={
              destinationLatitude && destinationLongitude
                ? {
                    latitude: parseFloat(destinationLatitude),
                    longitude: parseFloat(destinationLongitude),
                  }
                : null
            }
            selectionMode={selectionMode}
            onLocationSelect={handleLocationSelect}
          />
        </section>

        {/* Results */}
        {(recommendedShelter || route?.metrics) && (
          <section className="results-grid">
            {recommendedShelter && (
              <div className="result-card shelter-card">
                <div className="result-icon">🏥</div>
                <div>
                  <p className="card-label">RECOMMENDED SHELTER</p>
                  <h2>{recommendedShelter.name}</h2>
                  <p className="capacity">
                    Available Capacity
                    <strong>{recommendedShelter.available_capacity}</strong>
                  </p>
                </div>
              </div>
            )}

            {route && route.metrics && (
              <div className="route-information">
                <div className="metrics-header">
                  <div>
                    <p className="card-label">ROUTE ANALYSIS</p>
                    <h2>Evacuation Metrics</h2>
                  </div>
                </div>

                <div className="metrics-grid">
                  <div className="metric">
                    <span>Distance</span>
                    <strong>
                      {route.metrics.total_distance.toFixed(0)}
                      <small> m</small>
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Travel Time</span>
                    <strong>
                      {route.metrics.total_travel_time.toFixed(0)}
                      <small> sec</small>
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Average Risk</span>
                    <strong>{route.metrics.average_risk.toFixed(3)}</strong>
                  </div>

                  <div className="metric">
                    <span>Maximum Risk</span>
                    <strong>{route.metrics.maximum_risk.toFixed(3)}</strong>
                  </div>

                  <div className="metric">
                    <span>Road Segments</span>
                    <strong>{route.metrics.road_count}</strong>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;