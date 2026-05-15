# Legal AI Frontend

Modern React frontend for the Legal AI Document Processing System.

## Features

- 📤 **Document Upload** - Drag & drop interface with real-time processing feedback
- 📄 **Document Management** - View, search, and manage processed documents
- ✨ **Draft Generation** - Interactive draft creation with multiple types
- 📊 **Pattern Insights** - Visualize learned patterns from operator edits
- 🎨 **Modern UI** - Clean, responsive design with TailwindCSS

## Tech Stack

- **React 18** - UI framework
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first CSS
- **Axios** - HTTP client
- **React Router** - Navigation
- **Lucide React** - Beautiful icons
- **React Hot Toast** - Toast notifications

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker

```bash
# Build image
docker build -t legal-ai-frontend .

# Run container
docker run -p 3000:3000 legal-ai-frontend
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx          # Main dashboard
│   │   ├── DocumentUpload.jsx     # Upload interface
│   │   ├── DocumentList.jsx       # Document management
│   │   ├── DraftGeneration.jsx    # Draft creation
│   │   └── PatternInsights.jsx    # Pattern visualization
│   ├── services/
│   │   └── api.js                 # API client
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## API Integration

The frontend communicates with the backend API at `http://localhost:8000` by default.

### Key Endpoints Used

- `POST /documents/upload` - Upload documents
- `GET /documents` - List documents
- `DELETE /documents/{id}` - Delete document
- `POST /drafts/generate` - Generate draft
- `POST /drafts/{id}/edit` - Submit edit
- `GET /patterns` - Get patterns
- `POST /patterns/extract` - Extract patterns

## Features Overview

### Dashboard
- System status monitoring
- Quick stats (documents, patterns)
- Quick action cards
- How it works guide

### Document Upload
- Drag & drop file upload
- Real-time processing feedback
- Extracted fields display
- Processing notes

### Document List
- Search functionality
- Document details
- Delete documents
- Status badges

### Draft Generation
- Multi-document selection
- Draft type selection
- Additional context input
- Edit mode with learning
- Evidence display

### Pattern Insights
- Pattern extraction
- Confidence scoring
- Before/after examples
- Grouped by draft type

## Customization

### Colors

Edit `tailwind.config.js` to customize the color scheme:

```js
colors: {
  primary: {
    // Your custom colors
  }
}
```

### API URL

Change the API URL in `.env`:

```env
VITE_API_URL=https://your-api-url.com
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
