# UpsetIQ Mobile App

React Native mobile application for UpsetIQ - Live Upset Intelligence for sports betting insights.

## Screenshot

![UpsetIQ Mobile App Home Screen](../docs/screenshots/app-home-screen.png)

Home screen displaying game cards with upset probability scores (UPS), risk indicators, probability breakdowns, and sport filtering options.

## Tech Stack

- **React Native** with Expo
- **TypeScript** for type safety
- **NativeWind** (Tailwind CSS for React Native)
- **React Navigation** for routing

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
# Start Expo development server
npx expo start

# Or run on specific platform
npx expo run:ios
npx expo run:android
```

### 3. Configure API Endpoint

Update the API base URL in `src/services/api.ts` to point to your backend:

```typescript
const API_BASE_URL = 'http://localhost:8000';  // Development
// const API_BASE_URL = 'https://your-api.com';  // Production
```

## Project Structure

```text
frontend/
├── App.tsx                 # App entry point
├── app.json               # Expo configuration
├── index.ts               # Register app
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── GameCard.tsx
│   │   ├── UPSGauge.tsx
│   │   └── ...
│   ├── screens/           # Screen components
│   │   ├── HomeScreen.tsx
│   │   ├── GameDetailScreen.tsx
│   │   └── ...
│   ├── navigation/        # Navigation setup
│   │   └── AppNavigator.tsx
│   ├── services/          # API and external services
│   │   └── api.ts
│   ├── context/           # React Context providers
│   ├── theme/             # Colors, typography, spacing
│   ├── types/             # TypeScript type definitions
│   ├── utils/             # Utility functions
│   └── data/              # Mock data for development
├── assets/                # Images, icons, fonts
├── ios/                   # iOS native code
├── android/               # Android native code
├── babel.config.js        # Babel configuration
├── metro.config.js        # Metro bundler config
├── tailwind.config.js     # Tailwind/NativeWind config
├── tsconfig.json          # TypeScript configuration
└── package.json           # Node dependencies
```

## Features

### Game Board

- View upcoming games with upset probability
- Sort by UPS, date, or sport
- Filter by sport (NFL, NBA, MLB, etc.)

### Game Details

- Full prediction breakdown
- Key drivers for upset potential
- Market signals and trends
- Team injury reports (via SportsDataIO)

### Upset Alerts

- Set custom UPS thresholds
- Push notifications when thresholds crossed

### Leaderboard

- Track prediction accuracy
- Compete with other users

## Styling

This app uses **NativeWind** for styling, which brings Tailwind CSS to React Native:

```tsx
<View className="flex-1 bg-gray-900 p-4">
  <Text className="text-white text-xl font-bold">
    Upset Alert!
  </Text>
</View>
```

## API Integration

The app connects to the FastAPI backend for:

- Game data with predictions (`/games`)
- Injury reports (`/injuries`)
- Team standings (`/standings`)
- Live scores (`/scores/live`)
- News feed (`/news`)

See `../backend/README.md` for full API documentation.

## Building for Production

### iOS

```bash
npx expo run:ios --configuration Release
```

### Android

```bash
npx expo run:android --variant release
```

## Environment Variables

Create a `.env` file for environment-specific configuration:

```env
API_BASE_URL=https://api.upsetiq.com
```
