import { EventEmitter } from 'events'

// Webhook event types
export type WebhookEventType = 
  | 'job_posting_status_update'
  | 'job_posting_completed'
  | 'job_posting_failed'

// Webhook event data
export interface WebhookEvent {
  type: WebhookEventType
  job_posting_id: string
  status: string
  data?: any
  timestamp: string
}

// Webhook service for handling real-time updates
class WebhookService extends EventEmitter {
  private isConnected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private eventSource: EventSource | null = null
  private heartbeatInterval: NodeJS.Timeout | null = null

  constructor() {
    super()
    this.setMaxListeners(50) // Allow many listeners
  }

  // Connect to webhook endpoint
  connect(): void {
    if (this.isConnected) {
      console.log('Webhook service already connected')
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.warn('No auth token found, cannot connect to webhooks')
        return
      }

      // Create EventSource connection to webhook endpoint
      const webhookUrl = `${import.meta.env.API_BASE_URL || 'http://localhost:8000'}/api/webhooks/job-postings?token=${token}`
      this.eventSource = new EventSource(webhookUrl)

      this.eventSource.onopen = () => {
        console.log('Webhook connection established')
        this.isConnected = true
        this.reconnectAttempts = 0
        this.emit('connected')
      }

      this.eventSource.onmessage = (event) => {
        try {
          const webhookEvent: WebhookEvent = JSON.parse(event.data)
          this.handleWebhookEvent(webhookEvent)
        } catch (error) {
          console.error('Failed to parse webhook event:', error)
        }
      }

      this.eventSource.onerror = (error) => {
        console.error('Webhook connection error:', error)
        this.isConnected = false
        this.emit('disconnected')
        this.handleReconnection()
      }

      // Start heartbeat to keep connection alive
      this.startHeartbeat()

    } catch (error) {
      console.error('Failed to connect to webhooks:', error)
      this.handleReconnection()
    }
  }

  // Disconnect from webhook endpoint
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }

    this.isConnected = false
    this.emit('disconnected')
  }

  // Handle webhook events
  private handleWebhookEvent(event: WebhookEvent): void {
    console.log('Received webhook event:', event)
    
    // Emit specific event types
    this.emit(event.type, event)
    
    // Emit general webhook event
    this.emit('webhook_event', event)
  }

  // Handle reconnection logic
  private handleReconnection(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      this.emit('max_reconnect_attempts_reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // Exponential backoff
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      this.connect()
    }, delay)
  }

  // Start heartbeat to keep connection alive
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.eventSource) {
        // Send ping to keep connection alive
        this.eventSource.dispatchEvent(new MessageEvent('ping'))
      }
    }, 30000) // Ping every 30 seconds
  }

  // Subscribe to specific job posting updates
  subscribeToJobPosting(jobPostingId: string, callback: (event: WebhookEvent) => void): () => void {
    const handler = (event: WebhookEvent) => {
      if (event.job_posting_id === jobPostingId) {
        callback(event)
      }
    }

    this.on('webhook_event', handler)
    
    // Return unsubscribe function
    return () => {
      this.off('webhook_event', handler)
    }
  }

  // Subscribe to job posting status updates
  subscribeToStatusUpdates(callback: (event: WebhookEvent) => void): () => void {
    this.on('job_posting_status_update', callback)
    
    return () => {
      this.off('job_posting_status_update', callback)
    }
  }

  // Subscribe to job posting completion
  subscribeToCompletion(callback: (event: WebhookEvent) => void): () => void {
    this.on('job_posting_completed', callback)
    
    return () => {
      this.off('job_posting_completed', callback)
    }
  }

  // Subscribe to job posting failures
  subscribeToFailures(callback: (event: WebhookEvent) => void): () => void {
    this.on('job_posting_failed', callback)
    
    return () => {
      this.off('job_posting_failed', callback)
    }
  }

  // Get connection status
  getConnectionStatus(): boolean {
    return this.isConnected
  }
}

// Create singleton instance
export const webhookService = new WebhookService()

// Auto-connect when auth token is available
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('auth_token')
  if (token) {
    webhookService.connect()
  }
}

export default webhookService
