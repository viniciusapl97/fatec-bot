import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ClipboardList, Pencil, Plus, Trash2 } from 'lucide-react'
import { createActivity, deleteActivity, listActivities, listSubjects, updateActivity } from '../api/resources'
import type { ActivityOut, ActivityType } from '../api/types'
import { ActivityTypeBadge, EmptyState, ErrorBanner, formatDate } from '../components/ui'

interface FormState {
  subject_id: string
  name: string
  due_date: string
  notes: string
}

const BLANK_FORM: FormState = { subject_id: '', name: '', due_date: '', notes: '' }

function toForm(activity: ActivityOut): FormState {
  return { subject_id: String(activity.subject_id), name: activity.name, due_date: activity.due_date, notes: activity.notes ?? '' }
}

const FILTERS: { label: string; value: ActivityType | undefined }[] = [
  { label: 'Todos', value: undefined },
  { label: 'Trabalhos', value: 'trabalho' },
  { label: 'Provas', value: 'prova' },
]

export function Activities() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<ActivityType | undefined>(undefined)
  const [newType, setNewType] = useState<ActivityType>('trabalho')
  const [editingId, setEditingId] = useState<number | 'new' | null>(null)
  const [form, setForm] = useState<FormState>(BLANK_FORM)
  const [formError, setFormError] = useState<unknown>(null)

  const activitiesQuery = useQuery({ queryKey: ['activities', filter], queryFn: () => listActivities(filter) })
  const subjectsQuery = useQuery({ queryKey: ['subjects'], queryFn: listSubjects })

  function startCreate() {
    setForm(BLANK_FORM)
    setNewType('trabalho')
    setFormError(null)
    setEditingId('new')
  }

  function startEdit(activity: ActivityOut) {
    setForm(toForm(activity))
    setFormError(null)
    setEditingId(activity.id)
  }

  function closeForm() {
    setEditingId(null)
    setFormError(null)
  }

  const createMutation = useMutation({
    mutationFn: () =>
      createActivity({ subject_id: Number(form.subject_id), activity_type: newType, name: form.name, due_date: form.due_date, notes: form.notes || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      closeForm()
    },
    onError: setFormError,
  })

  const updateMutation = useMutation({
    mutationFn: (id: number) =>
      updateActivity(id, { subject_id: Number(form.subject_id), name: form.name, due_date: form.due_date, notes: form.notes || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      closeForm()
    },
    onError: setFormError,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteActivity(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['activities'] }),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (editingId === 'new') createMutation.mutate()
    else if (editingId != null) updateMutation.mutate(editingId)
  }

  function handleDelete(activity: ActivityOut) {
    if (confirm(`Apagar "${activity.name}"?`)) deleteMutation.mutate(activity.id)
  }

  const saving = createMutation.isPending || updateMutation.isPending
  const sorted = [...(activitiesQuery.data ?? [])].sort((a, b) => a.due_date.localeCompare(b.due_date))

  return (
    <div>
      <div className="page-header">
        <h1>Atividades</h1>
        {editingId === null && (
          <button type="button" className="btn-primary" onClick={startCreate}>
            <Plus size={16} />
            Nova atividade
          </button>
        )}
      </div>

      <div className="filter-tabs">
        {FILTERS.map((f) => (
          <button key={f.label} type="button" className={filter === f.value ? 'active' : ''} onClick={() => setFilter(f.value)}>
            {f.label}
          </button>
        ))}
      </div>

      <ErrorBanner error={activitiesQuery.error} />

      {editingId !== null && (
        <form className="panel" onSubmit={handleSubmit}>
          <h2>{editingId === 'new' ? 'Nova atividade' : 'Editar atividade'}</h2>

          {editingId === 'new' && (
            <label>
              Tipo
              <select value={newType} onChange={(e) => setNewType(e.target.value as ActivityType)}>
                <option value="trabalho">Trabalho</option>
                <option value="prova">Prova</option>
              </select>
            </label>
          )}

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
            Nome
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Data
            <input required type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          </label>
          <label>
            Notas
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
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
              <th>Tipo</th>
              <th>Nome</th>
              <th>Matéria</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((activity) => (
              <tr key={activity.id}>
                <td data-label="Data">{formatDate(activity.due_date)}</td>
                <td data-label="Tipo">
                  <ActivityTypeBadge type={activity.activity_type} />
                </td>
                <td className="mobile-card-title">{activity.name}</td>
                <td data-label="Matéria">{activity.subject_name}</td>
                <td className="row-actions">
                  <button type="button" onClick={() => startEdit(activity)}>
                    <Pencil size={14} />
                    Editar
                  </button>
                  <button type="button" onClick={() => handleDelete(activity)}>
                    <Trash2 size={14} />
                    Apagar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sorted.length === 0 && <EmptyState icon={ClipboardList} message="Nenhuma atividade encontrada." />}
      </div>
    </div>
  )
}
