import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api } from '../lib/api'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('mock-token')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Authentication', () => {
    it('includes authorization header when token exists', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, name: 'Test User' }),
      })

      await api.getCurrentUser()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/me',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token',
          }),
        })
      )
    })

    it('handles logout correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })

      await api.logout()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token')
    })
  })

  describe('Assistant API', () => {
    it('calls query assistant endpoint correctly', async () => {
      const mockResponse = { response: 'AI response', repository_name: 'test-repo' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await api.queryAssistant({
        repository_id: 'repo-123',
        repository_name: 'test-repo',
        query: '/help',
        context_type: 'general',
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/assistant/query',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          }),
          body: JSON.stringify({
            repository_id: 'repo-123',
            repository_name: 'test-repo',
            query: '/help',
            context_type: 'general',
          }),
        })
      )

      expect(result).toEqual(mockResponse)
    })

    it('gets assistant status correctly', async () => {
      const mockStatus = { enabled: true, model: 'mistral-large-latest', service: 'Mistral AI' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStatus),
      })

      const result = await api.getAssistantStatus()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/assistant/status',
        expect.objectContaining({
          method: 'GET',
        })
      )

      expect(result).toEqual(mockStatus)
    })
  })

  describe('Error Handling', () => {
    it('handles 401 unauthorized by clearing token and redirecting', async () => {
      const mockLocation = { href: '' }
      Object.defineProperty(window, 'location', {
        value: mockLocation,
        writable: true,
      })

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      })

      await expect(api.getCurrentUser()).rejects.toThrow('Unauthorized')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(mockLocation.href).toBe('/login')
    })

    it('handles API errors correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Internal Server Error' }),
      })

      await expect(api.getCurrentUser()).rejects.toThrow('Internal Server Error')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(api.getCurrentUser()).rejects.toThrow('Network error')
    })
  })
})