# 🚀 Quick Start Guide - Transaction AI UI

## Step 1: Install Dependencies

```bash
cd ui
npm install
```

This will install:
- Next.js 14
- React 18
- Tailwind CSS
- Recharts (for visualizations)
- Lucide React (for icons)
- TypeScript

## Step 2: Make Sure API is Running

The UI needs the FastAPI backend running on `http://localhost:8000`.

**Option A: Using the running API**
```bash
# Check if API is already running
curl http://localhost:8000/health
```

**Option B: Start API manually**
```bash
# From project root
cd apps/api
python3 main.py
```

**Option C: Using Docker**
```bash
# From project root
docker-compose up -d
```

## Step 3: Start the UI

```bash
# From the ui/ directory
npm run dev
```

The UI will start on **http://localhost:3000**

## Step 4: Explore the Dashboard

Open your browser to [http://localhost:3000](http://localhost:3000)

### Available Tabs:

1. **Live Demo** 📊
   - Try sample transactions: "STARBUCKS COFFEE", "NETFLIX SUBSCRIPTION", etc.
   - See real-time categorization with confidence scores
   - View explanations and ensemble voting

2. **Ensemble Voting** 🎯
   - Visualize how Rule Engine, ML, and LLM vote
   - Interactive bar charts
   - Agreement rates

3. **System Health** 💚
   - Real-time status of all components
   - Auto-refreshes every 10 seconds
   - Component-level monitoring

4. **Feedback** 💬
   - Submit corrections
   - Help improve the system
   - Human-in-the-loop training

## Troubleshooting

### UI won't start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API connection errors
- Check API is running: `curl http://localhost:8000/health`
- Verify port 8000 is not blocked
- Check Next.js proxy config in `next.config.js`

### Port 3000 already in use
```bash
# Use a different port
PORT=3001 npm run dev
```

## What You'll See

### Stats Cards (Top of Dashboard)
- Total Processed: 16 transactions
- Avg Latency: 850ms
- Accuracy: 87.5%
- Review Rate: 43.8%

### Live Demo Features
- ✅ Instant categorization
- ✅ Confidence visualization
- ✅ Explanations for decisions
- ✅ Database persistence (shows record ID)
- ✅ Review flags for low confidence

### Ensemble Voting Chart
- Blue bar: Rule Engine (30% weight)
- Purple bar: ML Classifier (40% weight)
- Pink bar: LLM Reasoning (30% weight)
- Agreement counter shows consensus

### Health Dashboard
- 8 components monitored
- Green = healthy, Red = unhealthy
- Version info
- Last update timestamp

## Production Build

```bash
npm run build
npm start
```

## Enjoy! 🎉

You now have a beautiful, interactive dashboard showcasing your Transaction AI system!
