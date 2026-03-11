import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Login from '../pages/Login'

describe('Login Component', () => {
  beforeEach(() => {
    // Reset window.location mock
    Object.defineProperty(window, 'location', {
      value: {
        href: 'http://localhost:5173',
        assign: vi.fn(),
        replace: vi.fn(),
        reload: vi.fn(),
      },
      writable: true,
    })
  })

  it('renders login page with correct title', () => {
    render(<Login />)
    
    expect(screen.getByText('CloudHelm')).toBeInTheDocument()
    expect(screen.getByText('FinOps & DevOps Copilot')).toBeInTheDocument()
  })

  it('renders GitHub login button', () => {
    render(<Login />)
    
    const githubButton = screen.getByText('Continue with GitHub')
    expect(githubButton).toBeInTheDocument()
  })

  it('does not render Google login button', () => {
    render(<Login />)
    
    const googleButton = screen.queryByText('Continue with Google')
    expect(googleButton).not.toBeInTheDocument()
  })

  it('redirects to GitHub OAuth when GitHub button is clicked', () => {
    render(<Login />)
    
    const githubButton = screen.getByText('Continue with GitHub')
    fireEvent.click(githubButton)
    
    expect(window.location.href).toBe('http://localhost:8000/auth/github/login')
  })

  it('displays terms and privacy policy text', () => {
    render(<Login />)
    
    expect(screen.getByText(/Terms of Service and Privacy Policy/)).toBeInTheDocument()
  })

  it('has correct styling classes', () => {
    render(<Login />)
    
    const container = screen.getByText('CloudHelm').closest('div')
    expect(container).toHaveClass('text-center')
  })
})