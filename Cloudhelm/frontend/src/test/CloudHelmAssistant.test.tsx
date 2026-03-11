import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CloudHelmAssistant from '../components/CloudHelmAssistant'

// Mock the API
vi.mock('../lib/api', () => ({
  api: {
    queryAssistant: vi.fn(),
  },
}))

describe('CloudHelm Assistant', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders floating button when closed', () => {
    render(<CloudHelmAssistant />)
    
    const floatingButton = screen.getByRole('button')
    expect(floatingButton).toBeInTheDocument()
  })

  it('opens assistant popup when floating button is clicked', () => {
    render(<CloudHelmAssistant />)
    
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    expect(screen.getByText('CloudHelm Assistant')).toBeInTheDocument()
    expect(screen.getByText('v2.1 Model • Powered by Mistral AI')).toBeInTheDocument()
  })

  it('displays repository context when provided', () => {
    render(<CloudHelmAssistant repositoryName="test-repo" />)
    
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    expect(screen.getByText('Analyzing: test-repo')).toBeInTheDocument()
  })

  it('shows welcome message with CLI command buttons', () => {
    render(<CloudHelmAssistant />)
    
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    expect(screen.getByText('🤖 Show CLI commands')).toBeInTheDocument()
    expect(screen.getByText('🧪 Run tests')).toBeInTheDocument()
    expect(screen.getByText('🔍 Run linter')).toBeInTheDocument()
    expect(screen.getByText('🐛 Find errors')).toBeInTheDocument()
  })

  it('sets input value when CLI command button is clicked', () => {
    render(<CloudHelmAssistant />)
    
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    const testButton = screen.getByText('🧪 Run tests')
    fireEvent.click(testButton)
    
    const input = screen.getByPlaceholderText('Ask questions or use /help for CLI commands...')
    expect(input).toHaveValue('/test')
  })

  it('closes assistant when X button is clicked', () => {
    render(<CloudHelmAssistant />)
    
    // Open assistant
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    // Close assistant
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    expect(screen.queryByText('CloudHelm Assistant')).not.toBeInTheDocument()
  })

  it('handles input changes correctly', () => {
    render(<CloudHelmAssistant />)
    
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    const input = screen.getByPlaceholderText('Ask questions or use /help for CLI commands...')
    fireEvent.change(input, { target: { value: '/help' } })
    
    expect(input).toHaveValue('/help')
  })

  it('sends message on Enter key press', async () => {
    const { api } = await import('../lib/api')
    const mockQueryAssistant = vi.mocked(api.queryAssistant)
    mockQueryAssistant.mockResolvedValue({ response: 'Test response' })

    render(<CloudHelmAssistant />)
    
    const floatingButton = screen.getByRole('button')
    fireEvent.click(floatingButton)
    
    const input = screen.getByPlaceholderText('Ask questions or use /help for CLI commands...')
    fireEvent.change(input, { target: { value: '/help' } })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' })
    
    await waitFor(() => {
      expect(mockQueryAssistant).toHaveBeenCalledWith({
        repository_id: undefined,
        repository_name: undefined,
        query: '/help',
        context_type: 'general',
      })
    })
  })
})