# Antenna Digital Twin - Frontend

Professional engineering-grade React frontend for the Antenna Digital Twin platform.

## Design System

### Engineering Dark Neutral Theme
- **Backgrounds:** Deep Charcoal (#0E1116), Slate Gray (#1C2128)
- **Actions:** Steel Blue (#2F6FED), Muted Cyan (#4FB3C8)
- **Data Visualization:** Signal Green (#3DDC97), Warning Amber (#F4B860), Critical Red (#E5533D)
- **Typography:** Inter (primary), JetBrains Mono (monospace)

### Design Principles
- Flat, minimal, utility-driven
- No gradients, glassmorphism, or glowing effects
- Information-dense, compact spacing
- Colors only for state indication
- Professional RF lab software aesthetic

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/          # App layout components
│   │   ├── antenna/         # Antenna designer
│   │   ├── visualization/   # Plots and charts
│   │   ├── results/         # Results viewer
│   │   ├── optimization/    # Optimization UI
│   │   ├── validation/      # Validation dashboard
│   │   └── common/          # Shared components
│   ├── styles/              # Theme and global styles
│   ├── services/            # API and WebSocket clients
│   ├── hooks/               # React hooks
│   └── App.tsx              # Main app component
├── package.json
└── vite.config.ts
```

## Features

### Layout
- **Left Sidebar:** Project hierarchy and navigation
- **Central Workspace:** Main content area with tabs
- **Right Panel:** Parameters and confidence metrics
- **Bottom Status Bar:** System status and logs

### Components
- **Antenna Designer:** Parameter input forms
- **S11 Plot:** Frequency response visualization (Plotly)
- **Results Viewer:** EM simulation results
- **Optimization Panel:** Geometry tuning interface
- **Validation Dashboard:** Metrics and KPIs

## API Integration

The frontend connects to the backend API at `http://localhost:8000` by default.

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Technologies

- **React 18** with TypeScript
- **Vite** for build tooling
- **Plotly.js** for data visualization
- **Zustand** for state management
- **React Query** for data fetching
- **Axios** for HTTP requests

## Styling

- CSS Modules for component styles
- CSS Variables for theme tokens
- No CSS-in-JS libraries
- Monospace font for numerical values

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Minimum width: 1280px (engineering tool, not mobile)



















