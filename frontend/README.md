# Site Monitor Frontend

Modern React + TypeScript frontend for the Site Monitor application.

## Features

- 📊 **Dashboard**: Real-time uptime metrics, response time charts, and downtime timelines
- 🌐 **Site Management**: Add, edit, and remove monitored sites
- 🐛 **Debug Console**: DevTools-like interface with live event streaming
- 📈 **SLA Reports**: Comprehensive availability and performance reports
- ⚙️ **Settings**: Configure monitoring behavior

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and builds
- **Tailwind CSS** for styling
- **React Router** for routing
- **TanStack Query** for API state management
- **Zustand** for local state management
- **Recharts** for data visualization
- **Vitest** + React Testing Library for unit tests
- **Playwright** for e2e tests

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

The Vite dev server is configured to proxy API requests to the backend at `http://localhost:8000`.

### Building for Production

```bash
npm run build
```

Build artifacts will be generated in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Testing

### Unit Tests

```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### E2E Tests

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui
```

## Project Structure

```
src/
├── components/          # React components
│   ├── common/         # Reusable components (Button, Card, etc.)
│   ├── dashboard/      # Dashboard components
│   ├── debug/          # Debug console components
│   ├── layout/         # Layout components (Sidebar, Layout)
│   ├── sites/          # Site management components
│   ├── sla/            # SLA report components
│   └── settings/       # Settings components
├── hooks/              # Custom React hooks
├── lib/                # Library code (API client, utilities)
├── pages/              # Page components
├── stores/             # Zustand stores
├── test/               # Test setup
├── types/              # TypeScript types
├── utils/              # Utility functions
├── App.tsx             # Main app component
└── main.tsx            # Entry point
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## API Integration

The frontend communicates with the backend API through:

- REST endpoints for CRUD operations
- Server-Sent Events (SSE) for live debug event streaming
- Automatic retries and caching via TanStack Query

## Development Tips

- Hot module replacement (HMR) is enabled for fast development
- React Query DevTools can be added for debugging API state
- TypeScript strict mode is enabled for type safety
- Path aliases (`@/`) are configured for cleaner imports
