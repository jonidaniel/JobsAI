# Frontend Documentation

## Overview

The JobsAI frontend is a React application built with Vite that provides a user-friendly interface for job seekers to input their skills and preferences. The application collects user data through a multi-step questionnaire, sends it to the backend API, and downloads generated cover letters.

## Technology Stack

- **Framework**: React 19.2.0
- **Build Tool**: Vite 7.2.4
- **Styling**:
  - Tailwind CSS 3.4.18 (utility-first CSS)
  - Custom CSS files for component-specific styles
- **Language**: JavaScript (ES6+)
- **Package Manager**: npm

## Project Structure

```
frontend/
├── dist/                    # Production build output
├── node_modules/            # Dependencies
├── public/                  # Static assets
│   └── vite.svg
├── src/
│   ├── assets/              # Images and icons
│   │   ├── icons/
│   │   │   └── favicon.ico
│   │   └── imgs/
│   │       └── face.png
│   ├── components/         # React components
│   │   ├── Contact.jsx
│   │   ├── Hero.jsx
│   │   ├── NavBar.jsx
│   │   ├── QuestionSets.jsx
│   │   └── Search.jsx
│   ├── config/             # Configuration files
│   │   ├── api.js
│   │   ├── constants.js
│   │   ├── generalQuestions.js
│   │   ├── questionSetTitles.js
│   │   └── sliderData.js
│   ├── styles/             # CSS stylesheets
│   │   ├── App.css
│   │   ├── contact.css
│   │   ├── hero.css
│   │   ├── index.css
│   │   ├── nav.css
│   │   └── search.css
│   ├── App.jsx             # Root component
│   └── main.jsx            # Application entry point
├── eslint.config.js        # ESLint configuration
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── postcss.config.js        # PostCSS configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── vite.config.js          # Vite configuration
```

## Directory Organization

### `/src/components/`

React components that make up the application UI:

- **`App.jsx`**: Root component that orchestrates all page sections
- **`NavBar.jsx`**: Fixed navigation bar with links to page sections
- **`Hero.jsx`**: Landing section with main title and tagline
- **`Search.jsx`**: Main questionnaire component that handles form submission
- **`QuestionSets.jsx`**: Complex component managing 10 question sets with navigation
- **`Contact.jsx`**: Contact information section with links

### `/src/config/`

Configuration files containing constants, data structures, and API endpoints:

- **`api.js`**: API endpoint configuration and base URL
- **`constants.js`**: Application-wide constants (question set counts, slider ranges, etc.)
- **`generalQuestions.js`**: Configuration for the general questions set (labels, keys, options)
- **`questionSetTitles.js`**: Display titles for each question set
- **`sliderData.js`**: Technology data for slider-based question sets (8 sets)

### `/src/styles/`

Component-scoped CSS files:

- **`index.css`**: Global styles and Tailwind imports
- **`App.css`**: Application-level styles
- **`nav.css`**: Navigation bar styles
- **`hero.css`**: Hero section styles
- **`search.css`**: Search/questionnaire section styles
- **`contact.css`**: Contact section styles

### `/src/assets/`

Static assets (images, icons, fonts):

- **`icons/`**: Favicon and icon files
- **`imgs/`**: Image files used in components

## Component Architecture

### Component Hierarchy

```
App
├── NavBar
├── Hero
├── Search
│   └── QuestionSets
│       ├── QuestionSet (rendered 10 times)
│       │   ├── Slider (for technology questions)
│       │   ├── TextField (for text inputs)
│       │   ├── MultipleChoice (for checkboxes)
│       │   └── SingleChoice (for radio buttons)
│       └── Navigation arrows
└── Contact
```

### Key Components

#### `QuestionSets.jsx`

The most complex component, managing:

- **10 question sets** with navigation (prev/next buttons)
- **Form state management** for all inputs
- **Dynamic rendering** based on question set type:
  - General questions (index 0): Multiple choice and single choice
  - Slider question sets (indices 1-8): Technology experience sliders
  - Text-only set (index 9): Single text input

**Sub-components** (defined within `QuestionSets.jsx`):

- `Slider`: Range input for experience levels (0-7 years)
- `TextField`: Text input for additional information
- `MultipleChoice`: Checkbox group for multiple selections
- `SingleChoice`: Radio button group for single selection

#### `Search.jsx`

Orchestrates form submission:

1. Receives form data from `QuestionSets` via callback
2. Filters out empty values
3. Groups data by question set
4. Sends POST request to backend API
5. Downloads returned `.docx` file
6. Displays success/error messages

## Configuration Files

### `api.js`

```javascript
export const API_ENDPOINTS = {
  SUBMIT_FORM: `${API_BASE_URL}/api/endpoint`,
};
```

- Configures API base URL (defaults to `http://localhost:8000`)
- Supports environment variable `VITE_API_BASE_URL`
- Centralizes all API endpoints

### `constants.js`

Application-wide constants:

- `TOTAL_QUESTION_SETS`: 10
- `GENERAL_QUESTIONS_COUNT`: 5
- `SLIDER_MIN/MAX/DEFAULT`: Slider configuration (0-7)
- `QUESTION_SET_NAMES`: Kebab-case names for each question set
- `GENERAL_QUESTIONS_INDEX`: 0

### `generalQuestions.js`

Configuration for the general questions set:

- `GENERAL_QUESTION_LABELS`: Display labels for 5 questions
- `GENERAL_QUESTION_KEYS`: Form data keys (e.g., "job-level", "job-boards")
- Option arrays: `NAME_OPTIONS`, `JOB_BOARD_OPTIONS`, `DEEP_MODE_OPTIONS`, etc.

### `questionSetTitles.js`

Display titles for all 10 question sets, shown as headings above each set.

### `sliderData.js`

Technology data for 8 slider-based question sets:

- Languages, databases, cloud development, web frameworks, etc.
- Each set is an object mapping technology keys to display labels
- Currently stored as JSON strings (parsed at module load)

## Styling Approach

### Tailwind CSS

Utility-first CSS framework used for:

- Layout (flexbox, grid)
- Spacing (padding, margin)
- Colors and typography
- Responsive design

### Custom CSS

Component-specific styles in separate files:

- Scoped to component IDs (e.g., `#search`, `#hero`)
- Handles complex styling not easily achieved with Tailwind
- Maintains separation of concerns

### CSS Organization

- **Global styles**: `index.css` (Tailwind imports, root variables)
- **Component styles**: Individual files per component
- **App-level styles**: `App.css` for application-wide rules

## Data Flow

### Form Data Collection

1. **User Input**: User fills out questions across 10 question sets
2. **State Management**: `QuestionSets` component manages form state
3. **Callback**: `onFormDataChange` callback updates `Search` component state
4. **Submission**: User clicks "Find Jobs" button
5. **Processing**: `Search.handleSubmit()`:
   - Filters empty values
   - Groups data by question set
   - Transforms to backend format
6. **API Request**: POST to `/api/endpoint` with grouped data
7. **Response**: Backend returns `.docx` file as blob
8. **Download**: Browser downloads the file automatically

### Data Structure

**Frontend Form Data** (flat):

```javascript
{
  "job-level": ["Expert", "Intermediate"],
  "job-boards": ["Duunitori", "Jobly"],
  "deep-mode": "Yes",
  "javascript": 5,
  "python": 3,
  "text-field1": "Additional languages...",
  ...
}
```

**Backend Payload** (grouped by question set):

```javascript
{
  "general": [
    {"job-level": ["Expert", "Intermediate"]},
    {"job-boards": ["Duunitori", "Jobly"]},
    {"deep-mode": "Yes"},
    {"cover-letter-num": "5"},
    {"cover-letter-style": "Professional"}
  ],
  "languages": [
    {"javascript": 5},
    {"python": 3},
    {"text-field1": "Additional languages..."}
  ],
  ...
}
```

## Development Setup

### Prerequisites

- Node.js (v18 or higher recommended)
- npm

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Starts Vite dev server at `http://localhost:5173` (default port).

Features:

- Hot Module Replacement (HMR)
- Fast refresh
- Source maps

### Linting

```bash
npm run lint
```

Runs ESLint to check code quality and catch errors.

### Building for Production

```bash
npm run build
```

Creates optimized production build in `dist/` directory:

- Minified JavaScript
- Optimized CSS
- Asset optimization
- Tree-shaking

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for testing.

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production:

```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

**Note**: Vite requires the `VITE_` prefix for environment variables to be exposed to the client.

## Adding New Features

### Adding a New Question Set

1. **Update `constants.js`**:

   - Increment `TOTAL_QUESTION_SETS`
   - Add name to `QUESTION_SET_NAMES` array

2. **Update `questionSetTitles.js`**:

   - Add title to `QUESTION_SET_TITLES` array

3. **Add data to `sliderData.js`** (if slider-based):

   - Add new object to `SLIDER_DATA` array

4. **Update `QuestionSets.jsx`**:
   - Add rendering logic for new question set type (if needed)

### Adding a New General Question

1. **Update `generalQuestions.js`**:

   - Add label to `GENERAL_QUESTION_LABELS`
   - Add key to `GENERAL_QUESTION_KEYS`
   - Add options array (e.g., `NEW_QUESTION_OPTIONS`)

2. **Update `constants.js`**:

   - Increment `GENERAL_QUESTIONS_COUNT`

3. **Update `QuestionSets.jsx`**:
   - Add rendering logic in general questions section

### Adding a New Component

1. Create component file in `src/components/`
2. Import and use in `App.jsx` or parent component
3. Add component-specific CSS in `src/styles/` (if needed)
4. Import CSS in component file

### Adding a New API Endpoint

1. **Update `config/api.js`**:

   ```javascript
   export const API_ENDPOINTS = {
     SUBMIT_FORM: `${API_BASE_URL}/api/endpoint`,
     NEW_ENDPOINT: `${API_BASE_URL}/api/new-endpoint`,
   };
   ```

2. **Use in component**:

   ```javascript
   import { API_ENDPOINTS } from "../config/api";

   const response = await fetch(API_ENDPOINTS.NEW_ENDPOINT, {...});
   ```

## API Integration

### Backend Communication

The frontend communicates with the FastAPI backend:

- **Endpoint**: `/api/endpoint` (configurable via `VITE_API_BASE_URL`)
- **Method**: POST
- **Content-Type**: `application/json`
- **Request Body**: Grouped form data (see Data Flow section)
- **Response**: `.docx` file as blob with `Content-Disposition` header

### Error Handling

The `Search` component includes comprehensive error handling:

- **Network errors**: Connection failures
- **HTTP errors**: 400, 404, 500 status codes
- **User-friendly messages**: Technical errors converted to readable messages
- **Success feedback**: Auto-dismissing success message after 5 seconds

### File Download

The application automatically downloads the generated cover letter:

1. Receives blob from API response
2. Extracts filename from `Content-Disposition` header
3. Creates temporary download link
4. Programmatically triggers download
5. Cleans up blob URL and DOM elements

## Code Style

### Naming Conventions

- **Components**: PascalCase (e.g., `QuestionSets.jsx`)
- **Files**: PascalCase for components, camelCase for config
- **CSS files**: kebab-case (e.g., `search.css`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `TOTAL_QUESTION_SETS`)
- **Functions/Variables**: camelCase

### Component Structure

```javascript
/**
 * Component Description
 *
 * Detailed explanation of component purpose and usage.
 *
 * @param {type} propName - Description
 */
export default function ComponentName({ prop1, prop2 }) {
  // State declarations
  const [state, setState] = useState(initial);

  // Effects
  useEffect(() => {
    // Effect logic
  }, [dependencies]);

  // Event handlers
  const handleEvent = () => {
    // Handler logic
  };

  // Render
  return (
    // JSX
  );
}
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Consider code-splitting for large components
2. **Memoization**: Use `React.memo()` for expensive components
3. **State Management**: Minimize unnecessary re-renders
4. **Asset Optimization**: Images optimized during build
5. **Bundle Size**: Tree-shaking removes unused code

### Current Performance

- **Initial Load**: Fast due to Vite's optimized build
- **HMR**: Near-instant updates during development
- **Form State**: Efficient state management with React hooks
- **File Download**: Streamed blob download for large files

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ features required
- No IE11 support

## Troubleshooting

### Common Issues

1. **API Connection Failed**

   - Check `VITE_API_BASE_URL` in `.env`
   - Verify backend server is running
   - Check CORS settings on backend

2. **Styles Not Loading**

   - Verify CSS imports in components
   - Check Tailwind configuration
   - Ensure PostCSS is configured correctly

3. **Form Data Not Submitting**

   - Check browser console for errors
   - Verify API endpoint is correct
   - Check network tab for request details

4. **Build Errors**
   - Clear `node_modules` and reinstall
   - Check for syntax errors
   - Verify all imports are correct

## Future Improvements

Potential enhancements:

1. **TypeScript**: Add type safety
2. **State Management**: Consider Redux/Zustand for complex state
3. **Testing**: Add unit and integration tests
4. **Accessibility**: Improve ARIA labels and keyboard navigation
5. **Internationalization**: Add i18n support
6. **Progressive Web App**: Add PWA capabilities
7. **Error Boundaries**: Add React error boundaries
8. **Loading States**: Improve loading indicators
9. **Form Validation**: Client-side validation before submission
10. **Responsive Design**: Enhanced mobile experience

## Related Documentation

- [API Documentation](./api.md) - Backend API endpoints
- [Architecture](./architecture.md) - Overall system architecture
- [User Guide](./user-guide.md) - End-user documentation
- [Project Structure](./project-structure.md) - Full project organization
