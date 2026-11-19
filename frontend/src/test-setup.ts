// Runs before every test file: remove what each test rendered, so tests don't see each other's leftovers.
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => cleanup())
