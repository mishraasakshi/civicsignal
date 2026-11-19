import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ProgressTracker } from './ProgressTracker'

function states() {
  return screen.getAllByRole('listitem').map((li) => li.className.replace('tracker-step ', ''))
}

describe('ProgressTracker', () => {
  it('marks earlier stages done, the current one current and later ones pending', () => {
    render(<ProgressTracker current={2} />)
    expect(states()).toEqual(['done', 'done', 'current', 'pending'])
    expect(screen.getByText('In Progress').closest('li')?.getAttribute('aria-current')).toBe('step')
  })

  it('a brand-new complaint is only at the first stage', () => {
    render(<ProgressTracker current={0} />)
    expect(states()).toEqual(['current', 'pending', 'pending', 'pending'])
  })

  it('a resolved complaint shows every stage done', () => {
    render(<ProgressTracker current={3} allDone />)
    expect(states()).toEqual(['done', 'done', 'done', 'done'])
  })

  it('tells screen readers the state of each stage', () => {
    render(<ProgressTracker current={1} />)
    expect(screen.getByText('Submitted').textContent).toContain('(done)')
    expect(screen.getByText('Under Review').textContent).toContain('(current)')
    expect(screen.getByText('Resolved').textContent).toContain('(pending)')
  })

  it('shows dates under stages when given', () => {
    render(<ProgressTracker current={1} dates={['Aug 30, 2025']} />)
    expect(screen.getByText('Aug 30, 2025')).toBeTruthy()
  })
})
