# Expo Migration Notes

This document describes the assets and configurations preserved from the EpisodeGameAppExpo project during the frontend codebase unification.

## Preserved Assets

### Icons and Images
- `assets/adaptive-icon.png` - Android adaptive icon
- `assets/favicon.png` - Web favicon
- `assets/icon.png` - App icon
- `assets/splash-icon.png` - Splash screen icon

### Configuration Files
- `expo.app.json` - Expo configuration (renamed from app.json)
- `index.expo.ts` - Expo entry point (renamed from index.ts)

## Migration Summary

**Date**: January 2025
**Decision**: Standard React Native (EpisodeGameApp) chosen as canonical codebase
**Reason**: EpisodeGameApp contains advanced features including:
- A1 Decider workflow integration
- PythonBridgeService and SubtitleService
- Granular context architecture
- Comprehensive testing suite
- Backend integration
- Web platform support

**EpisodeGameAppExpo Status**: Deleted after asset preservation

## Future Expo Support

If Expo support is needed in the future:
1. Install Expo CLI and dependencies
2. Use the preserved `expo.app.json` as a starting point
3. Modify `index.expo.ts` as the entry point
4. Configure build scripts for Expo in package.json

## Build Configurations

The main project now supports:
- React Native mobile builds (iOS/Android)
- Web builds via webpack
- Potential future Expo builds using preserved configurations