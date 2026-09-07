import { api } from './api'

// Simple browser-compatible event emitter
class EventEmitter {
  private listeners: { [key: string]: Function[] } = {}

  setMaxListeners(_n: number) {
    return this
  }

  on(event: string, listener: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(listener)
    return this
  }

  off(event: string, listener: Function) {
    if (!this.listeners[event]) return this
    this.listeners[event] = this.listeners[event].filter(l => l !== listener)
    return this
  }

  emit(event: string, ...args: any[]) {
    if (!this.listeners[event]) return false
    this.listeners[event].forEach(listener => {
      try {
        listener(...args)
      } catch (error) {
        console.error('Error in event listener:', error)
      }
    })
    return true
  }

  removeAllListeners(event?: string) {
    if (event) {
      delete this.listeners[event]
    } else {
      this.listeners = {}
    }
    return this
  }

  hasActiveListeners(): boolean {
    return Object.keys(this.listeners).some(key => this.listeners[key].length > 0)
  }
}

// Generic webhook event types
export type WebhookEventType = 
  | 'job_posting_status_update'
  | 'job_posting_completed'
  | 'job_posting_failed'
  | 'application_status_update'
  | 'resume_generation_status_update'
  | 'resume_generation_completed'
  | 'resume_generation_failed'
  | 'user_notification'
  | 'system_alert'
  | 'heartbeat'
  | 'connected'
  | 'disconnected'

// Generic webhook event data
export interface WebhookEvent {
  type: WebhookEventType
  entity_type?: string // e.g., 'job_posting', 'application', 'resume'
  entity_id?: string   // ID of the entity being updated
  status?: string      // Status update
  data?: any           // Additional event-specific data
  timestamp: string
  user_id?: number      // Target user (for user-specific events)
}

// Webhook / Polling service for real-time status updates in serverless environment
class WebhookService extends EventEmitter {
  private isConnected = true
  private activePollers: Map<string, { interval: ReturnType<typeof setInterval>; lastStatus?: string; isFinished?: boolean }> = new Map()

  constructor() {
    super()
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.disconnect()
      })
    }
  }

  // Connect to webhook / polling service
  connect(): void {
    this.isConnected = true
    this.emit('connected')
  }

  forceConnect(): boolean {
    this.connect()
    return true
  }

  // Disconnect and stop all active polling
  disconnect(): void {
    this.activePollers.forEach(poller => clearInterval(poller.interval))
    this.activePollers.clear()
    this.isConnected = false
    this.emit('disconnected')
  }

  // Handle webhook events internally
  private handleWebhookEvent(event: WebhookEvent): void {
    console.log('Processed real-time status event:', event)
    this.emit(event.type, event)
    if (event.entity_type && event.entity_id) {
      this.emit(`${event.entity_type}_${event.entity_id}`, event)
    }
    this.emit('webhook_event', event)
  }

  // Start polling an entity until complete or failed
  private startEntityPolling(entityType: string, entityId: string): void {
    const key = `${entityType}:${entityId}`
    if (this.activePollers.has(key)) return

    const poll = async () => {
      try {
        if (entityType === 'job_posting') {
          const res = await api.get(`/api/job-postings/${entityId}`)
          const job = res.data
          if (job) {
            const currentStatus = job.status
            const poller = this.activePollers.get(key)
            if (!poller || poller.isFinished) return

            poller.lastStatus = currentStatus

            let eventType: WebhookEventType = 'job_posting_status_update'
            if (currentStatus === 'complete') eventType = 'job_posting_completed'
            else if (currentStatus === 'failed') eventType = 'job_posting_failed'

            if (currentStatus === 'complete' || currentStatus === 'failed') {
              poller.isFinished = true
              this.stopEntityPolling(entityType, entityId)
            }

            const event: WebhookEvent = {
              type: eventType,
              entity_type: 'job_posting',
              entity_id: entityId,
              status: currentStatus,
              data: {
                title: job.title,
                company: job.company,
                description: job.description,
                ...job,
              },
              timestamp: job.updated_at || new Date().toISOString(),
            }
            this.handleWebhookEvent(event)
          }
        } else if (entityType === 'resume_generation') {
          const res = await api.get(`/api/webhooks/status/${entityId}`)
          const data = res.data
          if (data && data.status !== 'unknown') {
            const currentStatus = data.status
            const poller = this.activePollers.get(key)
            if (!poller || poller.isFinished) return

            poller.lastStatus = currentStatus

            let eventType: WebhookEventType = 'resume_generation_status_update'
            if (currentStatus === 'complete') eventType = 'resume_generation_completed'
            else if (currentStatus === 'failed') eventType = 'resume_generation_failed'

            if (currentStatus === 'complete' || currentStatus === 'failed') {
              poller.isFinished = true
              this.stopEntityPolling(entityType, entityId)
            }

            const event: WebhookEvent = {
              type: eventType,
              entity_type: 'resume_generation',
              entity_id: entityId,
              status: currentStatus,
              data: data.data || { message: data.message },
              timestamp: data.updated_at || new Date().toISOString(),
            }
            this.handleWebhookEvent(event)
          }
        }
      } catch (err) {
        // Suppress temporary polling errors
      }
    }

    // Immediate first poll
    poll()
    // Poll every 2 seconds
    const interval = setInterval(poll, 2000)
    this.activePollers.set(key, { interval })
  }

  private stopEntityPolling(entityType: string, entityId: string): void {
    const key = `${entityType}:${entityId}`
    const poller = this.activePollers.get(key)
    if (poller) {
      clearInterval(poller.interval)
      this.activePollers.delete(key)
    }
  }

  // Subscribe to specific entity updates (e.g. job_posting or resume_generation)
  subscribeToEntity(entityType: string, entityId: string, callback: (event: WebhookEvent) => void): () => void {
    console.log(`Subscribing to ${entityType}:${entityId}`)

    if (!this.isConnected) {
      this.connect()
    }

    const handler = (event: WebhookEvent) => {
      if (event.entity_type === entityType && event.entity_id === entityId) {
        callback(event)
      }
    }

    this.on('webhook_event', handler)
    this.startEntityPolling(entityType, entityId)

    return () => {
      this.off('webhook_event', handler)
      this.stopEntityPolling(entityType, entityId)
      setTimeout(() => this.disconnectIfNoListeners(), 100)
    }
  }

  // Subscribe to specific event types
  subscribeToEventType(eventType: WebhookEventType, callback: (event: WebhookEvent) => void): () => void {
    if (!this.isConnected) {
      this.connect()
    }

    this.on(eventType, callback)

    return () => {
      this.off(eventType, callback)
      setTimeout(() => this.disconnectIfNoListeners(), 100)
    }
  }

  // Subscribe to all events for a specific entity type
  subscribeToEntityType(entityType: string, callback: (event: WebhookEvent) => void): () => void {
    if (!this.isConnected) {
      this.connect()
    }

    const handler = (event: WebhookEvent) => {
      if (event.entity_type === entityType) {
        callback(event)
      }
    }

    this.on('webhook_event', handler)

    return () => {
      this.off('webhook_event', handler)
      setTimeout(() => this.disconnectIfNoListeners(), 100)
    }
  }

  getConnectionStatus(): boolean {
    return this.isConnected
  }

  disconnectIfNoListeners(): void {
    if (!this.hasActiveListeners() && this.activePollers.size === 0) {
      this.disconnect()
    }
  }
}

// Create singleton instance
export const webhookService = new WebhookService()
export default webhookService
