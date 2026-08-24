import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { GraduationCap, Pencil, Plus, Trash2 } from 'lucide-react'
import { createGrade, deleteGrade, listGrades, listSubjects, updateGrade } from '../api/resources'
import type { GradeOut } from '../api/types'
import { EmptyState, ErrorBanner } from '../components/ui'

interface FormState {
  subject_id: string
  name: string
  value: string
}

const BLANK_FORM: FormState = { subject_id: '', name: '', value: '' }

function toForm(grade: GradeOut): FormState {
  return { subject_id: String(grade.subject_id), name: grade.name, value: String(grade.value) }
}

export function Grades() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<number | 'new' | null>(null)
  const [form, setForm] = useState<FormState>(BLANK_FORM)
  const [formError, setFormError] = useState<unknown>(null)

  const gradesQuery = useQuery({ queryKey: ['grades'], queryFn: listGrades })
  const subjectsQuery = useQuery({ queryKey: ['subjects'], queryFn: listSubjects })

  function startCreate() {
    setForm(BLANK_FORM)
    setFormError(null)
    setEditingId('new')
  }

  function startEdit(grade: GradeOut) {
    setForm(toForm(grade))
    setFormError(null)
    setEditingId(grade.id)
  }

  function closeForm() {
    setEditingId(null)
    setFormError(null)
  }

  const createMutation = useMutation({
    mutationFn: () => createGrade({ subject_id: Number(form.subject_id), name: form.name, value: Number(form.value) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grades'] })
      closeForm()
    },
    onError: setFormError,
  })

  const updateMutation = useMutation({
    mutationFn: (id: number) => updateGrade(id, { name: form.name, value: Number(form.value) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grades'] })
      closeForm()
    },
    onError: setFormError,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteGrade(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grades'] }),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (editingId === 'new') createMutation.mutate()
    else if (editingId != null) updateMutation.mutate(editingId)
  }

  function handleDelete(grade: GradeOut) {
    if (confirm(`Apagar a nota "${grade.name}" de "${grade.subject_name}"?`)) deleteMutation.mutate(grade.id)
  }

  const saving = createMutation.isPending || updateMutation.isPending

  return (
    <div>
      <div className="page-header">
        <h1>Notas</h1>
        {editingId === null && (
          <button type="button" className="btn-primary" onClick={startCreate}>
            <Plus size={16} />
            Nova nota
          </button>
        )}
      </div>

      <ErrorBanner error={gradesQuery.error} />

      {editingId !== null && (
        <form className="panel" onSubmit={handleSubmit}>
          <h2>{editingId === 'new' ? 'Nova nota' : 'Editar nota'}</h2>

          {editingId === 'new' && (
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
          )}
          <label>
            Nome
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Valor
            <input required type="number" min={0} step="0.01" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
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
              <th>Matéria</th>
              <th>Nome</th>
              <th>Valor</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {gradesQuery.data?.map((grade) => (
              <tr key={grade.id}>
                <td data-label="Matéria">{grade.subject_name}</td>
                <td className="mobile-card-title">{grade.name}</td>
                <td data-label="Valor">{grade.value}</td>
                <td className="row-actions">
                  <button type="button" onClick={() => startEdit(grade)}>
                    <Pencil size={14} />
                    Editar
                  </button>
                  <button type="button" onClick={() => handleDelete(grade)}>
                    <Trash2 size={14} />
                    Apagar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {gradesQuery.data?.length === 0 && <EmptyState icon={GraduationCap} message="Nenhuma nota lançada." />}
      </div>
    </div>
  )
}
