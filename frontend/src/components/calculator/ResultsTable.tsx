import React from 'react';

export interface ResultRow {
  symbol: string;
  label: string;
  value: number | string;
  unit: string;
}

interface ResultsTableProps {
  title: string;
  rows: ResultRow[];
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ title, rows }) => (
  <div className="results-table-wrap">
    <h3 className="results-table-title">{title}</h3>
    <table className="results-table">
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Quantity</th>
          <th>Value</th>
          <th>Unit</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={`${r.symbol}-${i}`}>
            <td className="mono">{r.symbol}</td>
            <td>{r.label}</td>
            <td className="mono">{r.value}</td>
            <td>{r.unit}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
