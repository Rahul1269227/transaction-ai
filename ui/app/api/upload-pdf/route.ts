import { NextRequest, NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Get the form data from the request
    const formData = await request.formData()
    const file = formData.get('file')

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { detail: 'No file provided' },
        { status: 400 }
      )
    }

    console.log(`[PDF Upload] Receiving file: ${file.name}, size: ${file.size} bytes`)

    // Create a new FormData to send to the backend
    const backendFormData = new FormData()

    // Convert File to Blob and append
    const blob = new Blob([await file.arrayBuffer()], { type: file.type })
    backendFormData.append('file', blob, file.name)

    console.log(`[PDF Upload] Forwarding to backend: ${API_BASE_URL}/upload-pdf`)

    // Forward to the FastAPI backend with extended timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000) // 5 minutes

    try {
      const response = await fetch(`${API_BASE_URL}/upload-pdf`, {
        method: 'POST',
        body: backendFormData,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      console.log(`[PDF Upload] Backend response status: ${response.status}`)

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`[PDF Upload] Backend error: ${errorText}`)

        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { detail: `Backend error: ${response.status}` }
        }

        return NextResponse.json(
          errorData,
          { status: response.status }
        )
      }

      const data = await response.json()
      console.log(`[PDF Upload] Success: ${data.total} transactions processed`)

      return NextResponse.json(data)

    } catch (fetchError: any) {
      clearTimeout(timeoutId)

      if (fetchError.name === 'AbortError') {
        console.error('[PDF Upload] Request timeout')
        return NextResponse.json(
          { detail: 'Request timed out after 5 minutes. Please try a smaller PDF.' },
          { status: 504 }
        )
      }

      throw fetchError
    }

  } catch (error: any) {
    console.error('[PDF Upload] Error:', error)

    return NextResponse.json(
      { detail: error.message || 'Unknown error processing PDF' },
      { status: 500 }
    )
  }
}

// Configure route for file uploads
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const maxDuration = 300 // 5 minutes
