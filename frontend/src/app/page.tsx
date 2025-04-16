"use client"; // Add this directive for client-side hooks

import React, { useState, useEffect } from 'react';
import GridPlot from '@/components/GridPlot'; // Assuming GridPlot component will be created

// Define types for positions
type PositionInput = { x: string; y: string };
type Position = { x: number; y: number };

export default function Home() {
  const [numAnchors, setNumAnchors] = useState<number | null>(null);
  const [anchorPositionsInput, setAnchorPositionsInput] = useState<PositionInput[]>([]);
  const [isSetupComplete, setIsSetupComplete] = useState<boolean>(false);
  const [targetPosition, setTargetPosition] = useState<Position | null>(null);
  const [anchorsToPlot, setAnchorsToPlot] = useState<Position[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [mode, setMode] = useState<boolean>(false);


  const API_BASE_URL = "http://localhost:5001"; // Your Flask server URL

  const handleSendToNode = async () => {
    const newMode = !mode;
    setMode(newMode);
    try {
      const response = await fetch(`${API_BASE_URL}/toggle_mode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: newMode }), // Send the mode toggle to the server
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP error! status: ${response.status}`);
      }

      // Handle response success (optional: log success or show a message)
      console.log("Mode toggled successfully!");
    } catch (err: any) {
      console.error("Error sending command to the server:", err);
    }
  };

 
  

  // Handle change in number of anchors selection
  const handleNumAnchorsChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const num = parseInt(event.target.value, 10);
    if (num >= 3 && num <= 5) {
      setNumAnchors(num);
      // Initialize position inputs with empty strings
      setAnchorPositionsInput(Array(num).fill({ x: '', y: '' }));
      setIsSetupComplete(false); // Reset setup status if number changes
      setTargetPosition(null);
      setAnchorsToPlot([]);
      setError(null);
    } else {
        setNumAnchors(null); // Reset if invalid selection occurs
        setAnchorPositionsInput([]);
    }
  };

  // Handle changes in position input fields
  const handlePositionInputChange = (index: number, axis: 'x' | 'y', value: string) => {
    const updatedPositions = [...anchorPositionsInput];
    updatedPositions[index] = { ...updatedPositions[index], [axis]: value };
    setAnchorPositionsInput(updatedPositions);
  };

  // Validate inputs before submission
  const validateInputs = (): Position[] | null => {
    if (!numAnchors) return null;
    const positions: Position[] = [];
    for (let i = 0; i < numAnchors; i++) {
      const xVal = parseFloat(anchorPositionsInput[i].x);
      const yVal = parseFloat(anchorPositionsInput[i].y);
      if (isNaN(xVal) || isNaN(yVal)) {
        setError(`Invalid number format for Anchor ${i + 1}. Please enter numeric coordinates.`);
        return null;
      }
      positions.push({ x: xVal, y: yVal });
    }
    setError(null); // Clear error if validation passes
    return positions;
  };

  // Handle form submission to set up anchors
  const handleSubmitAnchors = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!numAnchors) {
        setError("Please select the number of anchors.");
        return;
    }

    const validatedPositions = validateInputs();
    if (!validatedPositions) {
      // Error state is already set by validateInputs
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/anchors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          num: numAnchors,
          positions: validatedPositions.map(p => [p.x, p.y]), // Format for backend
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP error! status: ${response.status}`);
      }

      if (result.success) {
        setAnchorsToPlot(validatedPositions);
        setIsSetupComplete(true);
        setError(null);
        setTargetPosition(null); // Reset target position on new setup
        console.log("Anchors configured successfully!");
      } else {
          throw new Error(result.error || "Failed to configure anchors.");
      }
    } catch (err: any) {
      console.error("Error setting up anchors:", err);
      setError(err.message || "An unexpected error occurred.");
      setIsSetupComplete(false);
      setAnchorsToPlot([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Effect for polling the trilaterate endpoint
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    const fetchTargetPosition = async () => {
        if (!isSetupComplete) return;
        try {
            const response = await fetch(`${API_BASE_URL}/trilaterate`);
            const data = await response.json();
            if (!response.ok) {
                 // Display backend errors, but don't stop polling unless critical
                console.warn(`Error fetching position: ${data.error || response.statusText}`);
                // Optionally set an error state specific to polling
                // setError(`Polling error: ${data.error || response.statusText}`);
                setTargetPosition(null); // Clear position if error occurs
            } else if (data.position) {
                setTargetPosition({ x: data.position[0], y: data.position[1] });
                // Clear polling-specific errors if successful
                // setError(null); 
            } else {
                 // Handle cases where position is null but response is OK (e.g., waiting for data)
                console.log("Waiting for position data...");
                setTargetPosition(null);
            }
        } catch (err) {
            console.error("Network or other error fetching position:", err);
            // setError("Failed to connect to server for position updates.");
            setTargetPosition(null);
            // Consider stopping polling if network errors persist
            // setIsSetupComplete(false); 
        }
    };

    if (isSetupComplete) {
      // Immediately fetch first position
      fetchTargetPosition(); 
      // Start polling every 1 second
      intervalId = setInterval(fetchTargetPosition, 1000);
    }

    // Cleanup function to clear the interval when the component unmounts
    // or when isSetupComplete becomes false
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isSetupComplete, API_BASE_URL]); // Re-run effect if setup status changes

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8 flex flex-col items-center font-sans">
      <h1 className="text-4xl font-bold mb-8">WNA Localization</h1>

      {/* Anchor Setup Form */}
      {!isSetupComplete && (
        <form onSubmit={handleSubmitAnchors} className="w-full max-w-lg bg-gray-800 p-6 rounded-lg shadow-lg mb-8">
          <h2 className="text-2xl font-semibold mb-6 text-center">Anchor Setup</h2>
          
          {/* Number of Anchors Selection */}
          <div className="mb-6">
            <label htmlFor="numAnchors" className="block text-sm font-medium text-gray-300 mb-2">Number of Anchors:</label>
            <select
              id="numAnchors"
              value={numAnchors ?? ''}
              onChange={handleNumAnchorsChange}
              required
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="" disabled>Select number (3-5)</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
            </select>
          </div>

          {/* Anchor Position Inputs */}
          {numAnchors && (
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-3 text-gray-300">Anchor Positions (X, Y):</h3>
              {anchorPositionsInput.map((pos, index) => (
                <div key={index} className="flex gap-4 mb-3 items-center">
                  <span className="text-gray-400 w-10">A{index + 1}:</span>
                  <input
                    type="number" // Use number type for better input control
                    step="any" // Allow decimals
                    placeholder="X" 
                    value={pos.x}
                    onChange={(e) => handlePositionInputChange(index, 'x', e.target.value)}
                    required
                    className="flex-1 p-2 bg-gray-700 border border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                  <input
                    type="number"
                    step="any"
                    placeholder="Y"
                    value={pos.y}
                    onChange={(e) => handlePositionInputChange(index, 'y', e.target.value)}
                    required
                    className="flex-1 p-2 bg-gray-700 border border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Submit Button */} 
          {numAnchors && (
             <button
                type="submit"
                disabled={isLoading}
                className={`w-full py-3 px-4 rounded-md text-white font-semibold transition-colors duration-200 ${isLoading ? 'bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
             >
                {isLoading ? 'Configuring...' : 'Configure Anchors & Start Tracking'}
             </button>
          )}

           {/* Error Display */} 
           {error && (
               <p className="mt-4 text-red-400 text-sm text-center">Error: {error}</p>
           )}
        </form>
      )}

      {/* Grid Plot Display */} 
      {isSetupComplete && (
        <div className="w-full max-w-3xl flex flex-col items-center">
          <h2 className="text-2xl font-semibold mb-4">Live Position</h2>
          <GridPlot 
              anchors={anchorsToPlot} 
              target={targetPosition} 
              // You might need to pass grid dimensions or calculate them dynamically
          />
          <button
             onClick={() => { 
                 setIsSetupComplete(false); 
                 setNumAnchors(null); 
                 setAnchorPositionsInput([]); 
                 setAnchorsToPlot([]);
                 setTargetPosition(null);
                 setError(null);
             }}
             className="mt-6 py-2 px-4 bg-red-600 hover:bg-red-700 rounded-md text-white font-semibold transition-colors duration-200"
          >
            Reset Configuration
          </button>
        </div>
      )}
            {/* Send Command to Node */}
      <div className="mt-8 w-full max-w-md bg-gray-800 p-6 rounded-lg shadow-lg">
        <h3 className="text-lg font-semibold text-center mb-4">Send Command to Node</h3>
        
          
          <button
            onClick={handleSendToNode}
            className="py-2 px-4 bg-green-600 hover:bg-green-700 rounded-md text-white font-semibold w-full"
          >
            Change Mode
          </button>
      </div>

    </div>
  );
}
