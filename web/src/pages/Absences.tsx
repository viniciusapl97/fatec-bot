import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarX2, Pencil, Plus, Trash2 } from 'lucide-react'
import { createAbsence, deleteAbsence, listAbsences, listSubjects, updateAbsence } from '../api/resources'
import type { AbsenceOut } from '../api/types'
import { EmptyState, ErrorBanner, formatDate } from '../components/ui'

interface FormState {
  subject_id: string
  absence_date: string
  quantity: string
  notes: string
}

const BLANK_FORM: FormState = { subject_id: '', absence_date: '', quantity: '1', notes: '' }

function toForm(absence: AbsenceOut): FormState {
  return { subject_id: String(absence.subject_id), absence_date: absence.absence_date, quantity: String(absence.quantity), notes: absence.notes ?? '' }
}

export function Absences() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<number | 'new' | null>(null)
  const [form, setForm] = useState<FormState>(BLANK_FORM)
  const [formError, setFormError] = useState<unknown>(null)

  const absencesQuery = useQuery({ queryKey: ['absences'], queryFn: listAbsences })
  const subjectsQuery = useQuery({ queryKey: ['subjects'], queryFn: listSubjects })

  function startCreate() {
    setForm(BLANK_FORM)
    setFormError(null)
    setEditingId('new')
  }

  function startEdit(absence: AbsenceOut) {
    setForm(toForm(absence))
    setFormError(null)
    setEditingId(absence.id)
  }

  function closeForm() {
    setEditingId(null)
    setFormError(null)
  }

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['absences'] })
    queryClient.invalidateQueries({ queryKey: ['subjects'] })
  }

  const createMutation = useMutation({
    mutationFn: () =>
      createAbsence({ subject_id: Number(form.subject_id), absence_date: form.absence_date, quantity: Number(form.quantity), notes: form.notes || null }),
    onSuccess: () => {
      invalidate()
      closeForm()
    },
    onError: setFormError,
  })

  const updateMutation = useMutation({
    mutationFn: (id: number) => updateAbsence(id, { quantity: Number(form.quantity) }),
    onSuccess: () => {
      invalidate()
      closeForm()
    },
    onError: setFormError,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAbsence(id),
    onSuccess: invalidate,
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (editingId === 'new') createMutation.mutate()
    else if (editingId != null) updateMutation.mutate(editingId)
  }

  function handleDelete(absence: AbsenceOut) {
    if (confirm(`Apagar essa falta de "${absence.subject_name}"?`)) deleteMutation.mutate(absence.id)
  }

  const saving = createMutation.isPending || updateMutation.isPending
  const sorted = [...(absencesQuery.data ?? [])].sort((a, b) => b.absence_date.localeCompare(a.absence_date))

  return (
    <div>
      <div className="page-header">
        <h1>Faltas</h1>
        {editingId === null && (
          <button type="button" className="btn-primary" onClick={startCreate}>
            <Plus size={16} />
            Nova falta
          </button>
        )}
      </div>

      <ErrorBanner error={absencesQuery.error} />

      {editingId !== null && (
        <form className="panel" onSubmit={handleSubmit}>
          <h2>{editingId === 'new' ? 'Nova falta' : 'Editar falta'}</h2>

          {editingId === 'new' && (
            <>
              <label>
                Matéria
                <select required value={form.subject_id} onChange={(e) => setForm({ ...form, subject_id: e.target.value })}>
                  <option value="" disabled>
                    Selecione…
                  </option>
                  {subjectsQuery.data?.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Data
                <input required type="date" value={form.absence_date} onChange={(e) => setForm({ ...form, absence_date: e.target.value })} />
              </label>
              <label>
                Notas
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </label>
            </>
          )}

          <label>
            Quantidade
            <input required type="number" min={1} value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
          </label>

          <ErrorBanner error={formError} />

          <div className="form-actions">
            <button type="submit" disabled={saving}>
              {saving ? 'Salvando…' : 'Salvar'}
            </button>
            <button type="button" onClick={closeForm}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Matéria</th>
              <th>Quantidade</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((absence) => (
              <tr key={absence.id}>
                <td data-label="Data">{formatDate(absence.absence_date)}</td>
                <td className="mobile-card-title">{absence.subject_name}</td>
                <td data-label="Quantidade">{absence.quantity}</td>
                <td className="row-actions">
                  <button type="button" onClick={() => startEdit(absence)}>
                    <Pencil size={14} />
                    Editar
                  </button>
                  <button type="button" onClick={() => handleDelete(absence)}>
                    <Trash2 size={14} />
                    Apagar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sorted.length === 0 && <EmptyState icon={CalendarX2} message="Nenhuma falta registrada." />}
      </div>
    </div>
  )
}
