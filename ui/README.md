# Transaction AI - UI Dashboard

Beautiful Next.js dashboard for the Transaction AI Categorization System.

## Features

- **Live Categorization Demo** - Test transaction categorization in real-time
- **Ensemble Voting Visualization** - See how Rule, ML, and LLM methods vote
- **Health Monitoring** - Real-time system health dashboard
- **Feedback Submission** - Human-in-the-loop correction mechanism
- **Beautiful UI** - Modern, responsive design with dark mode support

## Quick Start

### 1. Install Dependencies

```bash
cd ui
npm install
```

### 2. Start the API Backend

Make sure the FastAPI backend is running:

```bash
# From the project root
cd apps/api
python3 main.py

# OR using Docker
docker-compose up -d
```

The API should be accessible at `http://localhost:8000`

### 3. Start the UI Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## UI Components

### 📊 Live Demo Tab
- Enter any transaction description
- Click "Categorize" to see instant results
- View category, confidence, method, and explanations
- Try example transactions with one click

### 🎯 Ensemble Voting Tab
- Visualize how each method (Rule, ML, LLM) votes
- Interactive bar chart showing confidence levels
- See agreement rates across methods
- Understand the ensemble decision-making process

### 💚 System Health Tab
- Real-time health monitoring of all components
- Auto-refresh every 10 seconds
- Component-level status (Router, ML, LLM, DB, Cache)
- System version and uptime information

### 💬 Feedback Tab
- Submit corrections for miscategorized transactions
- Simple form for predicted vs. correct category
- Helps train and improve the system
- Immediate confirmation on submission

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Language**: TypeScript

## Configuration

The UI automatically proxies API requests to `http://localhost:8000` via Next.js rewrites (configured in `next.config.js`).

To change the API endpoint, edit `next.config.js`:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://your-api-host:8000/:path*',
    },
  ]
}
```

## Development

### File Structure

```
ui/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main dashboard
│   └── globals.css         # Global styles
├── components/
│   ├── StatsCards.tsx           # Statistics cards
│   ├── TransactionCategorizer.tsx  # Single transaction categorization
│   ├── BatchUpload.tsx          # Batch processing
│   ├── EnsembleVoting.tsx       # Voting visualization
│   ├── HealthDashboard.tsx      # System health monitoring
│   └── FeedbackForm.tsx         # User feedback
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Features Showcase

### Real-time Stats
- Total transactions processed
- Average latency
- System accuracy
- Review rate

### Interactive Visualizations
- Confidence bars
- Progress indicators
- Color-coded status indicators
- Responsive charts

### Dark Mode Support
- Automatic dark mode detection
- Beautiful gradients
- Optimized contrast

## API Integration

The UI integrates with the following API endpoints:

- `GET /health` - System health status
- `POST /categorize` - Single transaction categorization
- `POST /feedback` - Submit correction feedback

All requests are automatically proxied through Next.js.

## Production Deployment

### Build for Production

```bash
npm run build
npm start
```

### Docker Deployment

Create a `Dockerfile` in the `ui/` directory:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Build and run:

```bash
docker build -t transaction-ai-ui .
docker run -p 3000:3000 transaction-ai-ui
```

## Screenshots

### Live Demo
Interactive transaction categorization with real-time results, confidence scores, and explanations.

### Ensemble Voting
Visual breakdown of how each AI method votes, showing the power of ensemble decision-making.

### System Health
Comprehensive health monitoring showing all system components at a glance.

---

**Built with ❤️ using Next.js 14, Tailwind CSS, and TypeScript**
