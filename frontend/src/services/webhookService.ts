// Simple browser-compatible event emitter
class EventEmitter {
  private listeners: { [key: string]: Function[] } = {}

  setMaxListeners(_n: number) {
    // Browser doesn't need max listeners limit, but keeping API compatibility
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

  // Check if there are any active listeners
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
    
    // Set up automatic disconnection on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.disconnect()
      })
    }
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

      // Create EventSource connection to generic webhook endpoint
      const webhookUrl = `${import.meta.env.API_BASE_URL || 'http://localhost:8000'}/api/webhooks/events?token=${token}`
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

  // Force connect (useful for manual connection)
  forceConnect(): boolean {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      console.warn('No auth token found, cannot connect to webhooks')
      return false
    }
    
    this.connect()
    return true
  }

  // Disconnect from webhook endpoint
  disconnect(): void {
    console.log('Disconnecting webhook service')
    
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }

    this.isConnected = false
    this.reconnectAttempts = 0
    this.emit('disconnected')
  }

  // Handle webhook events
  private handleWebhookEvent(event: WebhookEvent): void {
    console.log('Received webhook event:', event)
    
    // Emit specific event types
    this.emit(event.type, event)
    
    // Emit entity-specific events
    if (event.entity_type && event.entity_id) {
      this.emit(`${event.entity_type}_${event.entity_id}`, event)
    }
    
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

  // Generic subscription methods
  
  // Subscribe to specific entity updates
  subscribeToEntity(entityType: string, entityId: string, callback: (event: WebhookEvent) => void): () => void {
    console.log(`Subscribing to ${entityType}:${entityId}, current connection status: ${this.isConnected}`)
    
    // Connect lazily if not already connected
    if (!this.isConnected) {
      console.log('Webhook not connected, attempting to connect...')
      this.connect()
    }

    const handler = (event: WebhookEvent) => {
      if (event.entity_type === entityType && event.entity_id === entityId) {
        callback(event)
      }
    }

    this.on('webhook_event', handler)
    
    // Return unsubscribe function
    return () => {
      this.off('webhook_event', handler)
      // Check if we should disconnect after unsubscribing
      setTimeout(() => this.disconnectIfNoListeners(), 100)
    }
  }

  // Subscribe to specific event types
  subscribeToEventType(eventType: WebhookEventType, callback: (event: WebhookEvent) => void): () => void {
    // Connect lazily if not already connected
    if (!this.isConnected) {
      this.connect()
    }

    this.on(eventType, callback)
    
    return () => {
      this.off(eventType, callback)
      // Check if we should disconnect after unsubscribing
      setTimeout(() => this.disconnectIfNoListeners(), 100)
    }
  }

  // Subscribe to all events for a specific entity type
  subscribeToEntityType(entityType: string, callback: (event: WebhookEvent) => void): () => void {
    // Connect lazily if not already connected
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
      // Check if we should disconnect after unsubscribing
      setTimeout(() => this.disconnectIfNoListeners(), 100)
    }
  }

  // Get connection status
  getConnectionStatus(): boolean {
    return this.isConnected
  }

  // Disconnect if no active listeners (useful for cleanup)
  disconnectIfNoListeners(): void {
    if (!this.hasActiveListeners()) {
      console.log('No active listeners, disconnecting webhook service')
      this.disconnect()
    }
  }
}

// Create singleton instance
export const webhookService = new WebhookService()

export default webhookService
