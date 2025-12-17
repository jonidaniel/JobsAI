# TypeScript Migration Plan

This document outlines the step-by-step migration from JavaScript to TypeScript.

## Migration Strategy

We'll migrate incrementally, starting with configuration files and utilities, then moving to components. This allows the app to continue working throughout the migration.

## Step 1: Install Dependencies

```bash
npm install --save-dev typescript @types/node
```

## Step 2: Create TypeScript Configuration

Create `tsconfig.json` with React + Vite optimized settings.

## Step 3: Create Type Definitions

- `vite-env.d.ts` - Vite environment variable types
- Type definitions for custom types (API responses, form data, etc.)

## Step 4: Migrate Configuration Files

1. `vite.config.js` → `vite.config.ts`
2. `vitest.config.js` → `vitest.config.ts`
3. Config files: `api.js`, `constants.js`, etc.

## Step 5: Migrate Utilities

1. `formDataTransform.js`
2. `validation.js`
3. `errorMessages.js`
4. `fileDownload.js`
5. `labelRenderer.jsx`

## Step 6: Migrate Hooks

1. `usePipelinePolling.js`
2. `useDownload.js`

## Step 7: Migrate Components (Small to Large)

1. Simple components: `ErrorMessage`, `SuccessMessage`, `Contact`, `Hero`, `NavBar`
2. Question components: `MultipleChoice`, `SingleChoice`, `Slider`, `TextField`
3. Complex components: `QuestionSet`, `QuestionSetList`, `ErrorBoundary`
4. Main component: `Search.jsx` (largest, do last)

## Step 8: Update Entry Point

- `main.jsx` → `main.tsx`
- `App.jsx` → `App.tsx`

## Step 9: Update ESLint

Configure ESLint to work with TypeScript files.

## Migration Order

The migration will be done in this order to minimize breaking changes:

1. ✅ Setup (tsconfig, types)
2. ✅ Config files
3. ✅ Utilities
4. ✅ Hooks
5. ✅ Small components
6. ✅ Medium components
7. ✅ Large components
8. ✅ Entry points
9. ✅ Tests

## Notes

- All `.jsx` files become `.tsx`
- All `.js` files become `.ts`
- Update all imports to use `.tsx`/`.ts` extensions (or remove extensions if using module resolution)
- Add proper type annotations gradually
- Use `any` temporarily if needed, but replace with proper types
