import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import * as resources from '../api/resources'
import type { SubjectOut } from '../api/types'
import { Subjects } from './Subjects'

vi.mock('../api/resources')

const BASE_SUBJECT: SubjectOut = {
  id: 1,
  name: 'Cálculo I',
  professor: 'Prof. Silva',
  day_of_week: 'Segunda',
  room: null,
  start_time: '07:30:00',
  end_time: '09:10:00',
  semestre: null,
  total_classes: 40,
  total_absences: 2,
  percent: 95,
  remaining_allowed: 8,
  at_risk: false,
  failed: false,
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Subjects />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Subjects page', () => {
  beforeEach(() => {
    vi.mocked(resources.listSubjects).mockReset().mockResolvedValue([BASE_SUBJECT])
    vi.mocked(resources.createSubject).mockReset()
    vi.mocked(resources.updateSubject).mockReset()
    vi.mocked(resources.deleteSubject).mockReset()
  })

  it('lists subjects with their computed attendance percentage', async () => {
    renderPage()

    expect(await screen.findByText('Cálculo I')).toBeInTheDocument()
    // (total_classes - total_absences) / total_classes = (40 - 2) / 40 = 95%
    expect(screen.getByText('95%')).toBeInTheDocument()
  })

  it('creates a subject from the form and closes it on success', async () => {
    const user = userEvent.setup()
    vi.mocked(resources.createSubject).mockResolvedValue({ ...BASE_SUBJECT, id: 2, name: 'Física I' })

    renderPage()
    await screen.findByText('Cálculo I')

    await user.click(screen.getByRole('button', { name: 'Nova matéria' }))
    await user.type(screen.getByLabelText('Nome'), 'Física I')
    await user.click(screen.getByText('Salvar'))

    await waitFor(() =>
      expect(resources.createSubject).toHaveBeenCalledWith(expect.objectContaining({ name: 'Física I', day_of_week: 'Segunda' })),
    )
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Nova matéria' })).not.toBeInTheDocument())
  })

  it('shows the backend schedule-conflict message inside the form on a 409', async () => {
    const user = userEvent.setup()
    vi.mocked(resources.createSubject).mockRejectedValue(
      new ApiError(409, 'Conflito de horário com "Cálculo I" (Segunda 07:30-09:10).'),
    )

    renderPage()
    await screen.findByText('Cálculo I')

    await user.click(screen.getByRole('button', { name: 'Nova matéria' }))
    await user.type(screen.getByLabelText('Nome'), 'Física I')
    await user.click(screen.getByText('Salvar'))

    expect(await screen.findByText(/Conflito de horário/)).toBeInTheDocument()
    // the form stays open so the user can fix the conflict, not discard their input
    expect(screen.getByRole('heading', { name: 'Nova matéria' })).toBeInTheDocument()
  })

  it('deletes a subject only after the user confirms', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(resources.deleteSubject).mockResolvedValue(undefined)

    renderPage()
    await screen.findByText('Cálculo I')

    await user.click(screen.getByText('Apagar'))

    expect(window.confirm).toHaveBeenCalled()
    await waitFor(() => expect(resources.deleteSubject).toHaveBeenCalledWith(1))
  })

  it('does not delete when the user cancels the confirmation', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    renderPage()
    await screen.findByText('Cálculo I')

    await user.click(screen.getByText('Apagar'))

    expect(resources.deleteSubject).not.toHaveBeenCalled()
  })
})
