# LangPlug Frontend

A Netflix-style German language learning platform built with React, TypeScript, and Vite.

## Features

- 🎬 Netflix-style interface for video selection
- 🎯 Interactive vocabulary learning games (Tinder-style word swiping)
- 📺 Custom video player with subtitle controls
- 🔐 Secure authentication system
- 📱 Responsive design for all devices
- ⚡ Fast development with Vite and Hot Module Replacement

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Styled Components** - Styling
- **Zustand** - State management
- **React Router** - Navigation
- **Framer Motion** - Animations
- **React Player** - Video playback
- **Axios** - API client

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Backend Integration

Make sure the backend API server is running on `http://localhost:8000`. The frontend is configured to proxy API requests to the backend.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── auth/           # Authentication components
│   ├── VideoSelection.tsx
│   ├── EpisodeSelection.tsx
│   ├── VocabularyGame.tsx
│   └── LearningPlayer.tsx
├── pages/              # Page components
├── services/           # API services
├── store/              # Zustand stores
├── types/              # TypeScript type definitions
├── styles/             # Global styles and themes
└── hooks/              # Custom React hooks
```

## Key Components

### Authentication Flow

- Login/Register forms with validation
- Protected routes with automatic redirection
- Session management with persistent storage

### Video Selection

- Netflix-style grid layout
- Series and episode browsing
- Subtitle availability indicators

### Vocabulary Game

- Tinder-style card swiping interface
- Progress tracking
- Difficulty level indicators
- Responsive touch/mouse controls

### Learning Player

- Custom video player controls
- 5-minute segment learning
- Subtitle toggle
- Progress tracking per segment

## Available Scripts

### Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### API Integration

- `npm run update-openapi` - **Update frontend after backend API changes** (exports spec + generates types + schemas)
- `npm run generate:client` - Generate TypeScript client from OpenAPI spec
- `npm run generate:schemas` - Generate Zod validation schemas from OpenAPI spec

**Workflow after backend API changes**:

```bash
# 1. Make changes to backend API routes
# 2. Update frontend to match:
npm run update-openapi

# This automatically:
# - Exports latest Backend/openapi.json
# - Generates TypeScript types in src/client/
# - Generates Zod schemas in src/schemas/api-schemas.ts
```

The frontend uses auto-generated code to stay in sync with the backend, ensuring type safety and validation consistency.

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
