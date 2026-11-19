import { describe, expect, it } from 'vitest'
import type { Status } from './api'
import { STAGES, stageIndex } from './labels'

describe('stageIndex: every backend status lands on the right tracker stage', () => {
  const expected: Record<Status, (typeof STAGES)[number]> = {
    Submitted: 'Submitted',
    'Under Review': 'Under Review',
    'Needs More Information': 'Under Review',
    Assigned: 'In Progress',
    'In Progress': 'In Progress',
    Resolved: 'Resolved',
    Closed: 'Resolved',
  }

  for (const [status, stage] of Object.entries(expected) as [Status, string][]) {
    it(`${status} -> ${stage}`, () => {
      expect(STAGES[stageIndex(status)]).toBe(stage)
    })
  }
})
