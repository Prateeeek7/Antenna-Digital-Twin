import React from 'react';
import Plot from 'react-plotly.js';
import './S11Plot.css';

interface S11PlotProps {
  frequency?: number[];
  s11Magnitude?: number[];
  confidenceLower?: number[];
  confidenceUpper?: number[];
}

export const S11Plot: React.FC<S11PlotProps> = ({
  frequency = [],
  s11Magnitude = [],
  confidenceLower,
  confidenceUpper,
}) => {
  const data: any[] = [
    {
      x: frequency,
      y: s11Magnitude,
      type: 'scatter',
      mode: 'lines',
      name: 'S11',
      line: { color: '#2F6FED', width: 2 },
    },
  ];

  if (confidenceLower && confidenceUpper) {
    data.push({
      x: [...frequency, ...frequency.slice().reverse()],
      y: [...confidenceUpper, ...confidenceLower.slice().reverse()],
      type: 'scatter',
      mode: 'lines',
      fill: 'toself',
      fillcolor: 'rgba(47, 111, 237, 0.2)',
      line: { color: 'transparent' },
      name: '95% CI',
      showlegend: true,
    });
  }

  const layout = {
    title: {
      text: 'S11 Frequency Response',
      font: { color: '#E6EDF3', size: 14 },
    },
    xaxis: {
      title: 'Frequency (GHz)',
      gridcolor: '#2D3748',
      color: '#9BA3AF',
    },
    yaxis: {
      title: 'S11 (dB)',
      gridcolor: '#2D3748',
      color: '#9BA3AF',
    },
    plot_bgcolor: '#0E1116',
    paper_bgcolor: '#1C2128',
    font: { color: '#E6EDF3', family: 'Inter' },
    margin: { l: 60, r: 20, t: 40, b: 60 },
  };

  return (
    <div className="s11-plot">
      <Plot data={data} layout={layout} config={{ displayModeBar: false }} />
    </div>
  );
};



















