import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Read the evaluation report from the reports folder
    const reportsPath = path.join(process.cwd(), '..', 'reports', 'evaluation_report.json')
    const reportData = fs.readFileSync(reportsPath, 'utf-8')
    const report = JSON.parse(reportData)

    return NextResponse.json(report)
  } catch (error) {
    console.error('Error reading evaluation report:', error)
    return NextResponse.json(
      { error: 'Failed to load evaluation report' },
      { status: 500 }
    )
  }
}
