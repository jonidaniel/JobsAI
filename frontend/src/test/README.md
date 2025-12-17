# Frontend Test Suite

This directory contains the test setup and configuration for the JobsAI frontend application.

## Test Framework

- **Vitest**: Fast unit test framework (Vite-native)
- **React Testing Library**: Component testing utilities
- **jsdom**: DOM environment for browser-like testing

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Test Structure

### Component Tests

- `components/questions/__tests__/`: Question component tests
  - `SingleChoice.test.jsx`: Radio button component tests
  - `MultipleChoice.test.jsx`: Checkbox component tests
  - `Slider.test.jsx`: Range slider component tests
  - `TextField.test.jsx`: Text input component tests
- `components/messages/__tests__/`: Message component tests
  - `ErrorMessage.test.jsx`: Error message display tests
- `components/__tests__/`: Main component tests
  - `Search.test.jsx`: Main search/pipeline component tests
  - `ErrorBoundary.test.jsx`: Error boundary tests

### Utility Tests

- `utils/__tests__/`: Utility function tests
  - `validation.test.js`: Form validation logic tests
  - `fileDownload.test.js`: File download utility tests

## Test Coverage

The test suite covers:

- ✅ Form validation logic
- ✅ File download functionality
- ✅ Question component rendering and interaction
- ✅ Form submission and API integration
- ✅ Progress polling
- ✅ Error handling
- ✅ Multiple document downloads
- ✅ Pipeline cancellation
- ✅ Error boundary behavior

## Writing New Tests

When adding new components or utilities:

1. Create test files in the same directory structure as source files
2. Use `__tests__` directory or `.test.jsx`/`.test.js` suffix
3. Follow existing test patterns:
   - Use `describe` blocks to group related tests
   - Use `it` or `test` for individual test cases
   - Use React Testing Library queries (`getByText`, `getByLabelText`, etc.)
   - Mock external dependencies (API calls, file operations)

## Example Test

```jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MyComponent from "../MyComponent";

describe("MyComponent", () => {
  it("should render correctly", () => {
    render(<MyComponent />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });
});
```
