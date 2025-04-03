import React from 'react';

type Position = { x: number; y: number };

interface GridPlotProps {
  anchors: Position[];
  target: Position | null;
  width?: number;
  height?: number;
  padding?: number;
  gridStep?: number;
}

const GridPlot: React.FC<GridPlotProps> = ({
  anchors,
  target,
  width = 500, // Default width
  height = 500, // Default height
  padding = 40, // Padding around the plot
  gridStep = 50, // Distance between grid lines
}) => {
  // Calculate plot area dimensions
  const plotWidth = width - 2 * padding;
  const plotHeight = height - 2 * padding;

  // Determine the bounds of the data to scale appropriately
  const allX = anchors.map(p => p.x).concat(target ? [target.x] : []);
  const allY = anchors.map(p => p.y).concat(target ? [target.y] : []);

  // Add a buffer around the min/max points to ensure points aren't exactly on the edge
  // Also handle the case where all points might be the same (or only one point exists)
  const minX = (allX.length > 0 ? Math.min(...allX) : 0) - 1;
  const maxX = (allX.length > 0 ? Math.max(...allX) : 0) + 1;
  const minY = (allY.length > 0 ? Math.min(...allY) : 0) - 1;
  const maxY = (allY.length > 0 ? Math.max(...allY) : 0) + 1;


  const rangeX = maxX - minX;
  const rangeY = maxY - minY;

  // Scaling functions: map data coordinates to SVG coordinates
  const scaleX = (x: number): number => {
    // Adjust scale if range is zero to avoid division by zero
    const effectiveRangeX = rangeX === 0 ? 1 : rangeX;
    return padding + ((x - minX) / effectiveRangeX) * plotWidth;
  };

  const scaleY = (y: number): number => {
     // Adjust scale if range is zero
    const effectiveRangeY = rangeY === 0 ? 1 : rangeY;
    // SVG y-coordinate is inverted (0 is top)
    return padding + plotHeight - ((y - minY) / effectiveRangeY) * plotHeight;
  };

  // Generate grid lines based on data range, not fixed steps
   const generateGridLines = () => {
    const lines = [];
    // Adjust grid line generation if range is very small or zero
    const numStepsX = rangeX > 0 ? Math.max(1, Math.floor(plotWidth / gridStep)) : 1;
    const numStepsY = rangeY > 0 ? Math.max(1, Math.floor(plotHeight / gridStep)) : 1;

    // Vertical lines
    for (let i = 0; i <= numStepsX; i++) {
      const x = padding + i * (plotWidth / numStepsX);
      lines.push(
        <line
          key={`v-${i}`}
          x1={x}
          y1={padding}
          x2={x}
          y2={height - padding}
          stroke="rgba(100, 100, 100, 0.5)" // Lighter grid lines
          strokeWidth="0.5"
        />
      );
    }
    // Horizontal lines
     for (let i = 0; i <= numStepsY; i++) {
      const y = padding + i * (plotHeight / numStepsY);
      lines.push(
        <line
          key={`h-${i}`}
          x1={padding}
          y1={y}
          x2={width - padding}
          y2={y}
          stroke="rgba(100, 100, 100, 0.5)"
          strokeWidth="0.5"
        />
      );
    }
    return lines;
  };

  return (
    <svg width={width} height={height} className="bg-gray-800 rounded-lg shadow-inner">
      {/* Plot Area Background (optional) */}
      <rect
        x={padding}
        y={padding}
        width={plotWidth}
        height={plotHeight}
        fill="rgba(55, 65, 81, 0.5)" // Slightly different bg for plot area
      />

      {/* Grid Lines */}
      {generateGridLines()}

      {/* Axes Lines */}
      {/* X-axis (representing y=0 if within view) */}
      {minY <= 0 && maxY >= 0 && (
         <line
            x1={padding}
            y1={scaleY(0)}
            x2={width - padding}
            y2={scaleY(0)}
            stroke="rgb(156 163 175)" // gray-400
            strokeWidth="1"
         />
      )}
       {/* Y-axis (representing x=0 if within view) */}
       {minX <= 0 && maxX >= 0 && (
         <line
            x1={scaleX(0)}
            y1={padding}
            x2={scaleX(0)}
            y2={height - padding}
            stroke="rgb(156 163 175)" // gray-400
            strokeWidth="1"
         />
       )}


      {/* Anchors */}
      {anchors.map((anchor, index) => (
        <g key={`anchor-${index}`} transform={`translate(${scaleX(anchor.x)}, ${scaleY(anchor.y)})`}>
           <circle
             r="8" // Anchor radius
             fill="rgba(59, 130, 246, 0.8)" // Blue-500 with some transparency
             stroke="white"
             strokeWidth="1"
           />
           <text
             fontSize="10"
             fill="white"
             textAnchor="middle"
             dy=".3em" // Vertically center
           >
            A{index + 1}
           </text>
         </g>
      ))}

      {/* Target */}
      {target && (
         <g transform={`translate(${scaleX(target.x)}, ${scaleY(target.y)})`}>
            <circle
              r="6" // Target radius
              fill="rgba(239, 68, 68, 0.9)" // Red-500
              stroke="white"
              strokeWidth="1"
              className="animate-pulse" // Simple pulse animation
             />
             {/* Optional: Target coordinates text */}
             <text
                 fontSize="10"
                 fill="white"
                 textAnchor="middle"
                 dy="-10" // Position above the target
              >
                 ({target.x.toFixed(2)}, {target.y.toFixed(2)})
             </text>
          </g>
      )}
        {/* Axes Labels (simple example) */}
        <text x={width / 2} y={height - padding / 4} fontSize="12" fill="gray" textAnchor="middle">X</text>
        <text x={padding / 4} y={height / 2} fontSize="12" fill="gray" textAnchor="middle" transform={`rotate(-90, ${padding / 4}, ${height / 2})`}>Y</text>

    </svg>
  );
};

export default GridPlot;