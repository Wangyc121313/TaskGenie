# TaskGenie Mobile

React Native mobile client for TaskGenie.

## Responsibilities

- display and manage tasks
- trigger AI task planning
- trigger AI day scheduling
- present calendar and statistics views

## Stack

- React Native 0.79
- React 19
- Context API
- custom hooks

## Development

```bash
npm install
npm start
```

Run on Android:

```bash
npm run android
```

Run on iOS:

```bash
npm run ios
```

## Backend URL

The API base URL is defined in:

`src/context/TaskContext.js`

Default values:

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://localhost:8000`
