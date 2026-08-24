import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Pencil, Plus, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { createSubject, deleteSubject, listSubjects, updateSubject } from '../api/resources'
import { DAYS_OF_WEEK } from '../api/types'
import type { SubjectCreate, SubjectOut } from '../api/types'
import { DayBadge, EmptyState, ErrorBanner, formatTime } from '../components/ui'

interface FormState {
  name: string
  professor: string
  day_of_week: string
  room: string
  start_time: string
  end_time: string
  semestre: string
  total_classes: string
}

const BLANK_FORM: FormState = {
  name: '',
  professor: '',
  day_of_week: DAYS_OF_WEEK[0],
  room: '',
  start_time: '',
  end_time: '',
  semestre: '',
  total_classes: '',
}

function toPayload(form: FormState): SubjectCreate {
  return {
    name: form.name,
    professor: form.professor || null,
    day_of_week: form.day_of_week as SubjectCreate['day_of_week'],
    room: form.room || null,
    start_time: form.start_time || null,
    end_time: form.end_time || null,
    semestre: form.semestre ? Number(form.semestre) : null,
    total_classes: form.total_classes ? Number(form.total_classes) : null,
  }
}

function toForm(subject: SubjectOut): FormState {
  return {
    name: subject.name,
    professor: subject.professor ?? '',
    day_of_week: subject.day_of_week,
    room: subject.room ?? '',
    start_time: subject.start_time ? subject.start_time.slice(0, 5) : '',
    end_time: subject.end_time ? subject.end_time.slice(0, 5) : '',
    semestre: subject.semestre != null ? String(subject.semestre) : '',
    total_classes: subject.total_classes != null ? String(subject.total_classes) : '',
  }
}

function attendancePercent(subject: SubjectOut): string {
  if (!subject.total_classes) return '—'
  const attended = subject.total_classes - subject.total_absences
  return `${Math.round((attended / subject.total_classes) * 100)}%`
}

export function Subjects() {
  const queryClient = useQueryClient()
  const subjectsQuery = useQuery({ queryKey: ['subjects'], queryFn: listSubjects })
  const [editingId, setEditingId] = useState<number | 'new' | null>(null)
  const [form, setForm] = useState<FormState>(BLANK_FORM)
  const [formError, setFormError] = useState<unknown>(null)

  function startCreate() {
    setForm(BLANK_FORM)
    setFormError(null)
    setEditingId('new')
  }

  function startEdit(subject: SubjectOut) {
    setForm(toForm(subject))
    setFormError(null)
    setEditingId(subject.id)
  }

  function closeForm() {
    setEditingId(null)
    setFormError(null)
  }

  const createMutation = useMutation({
    mutationFn: (payload: SubjectCreate) => createSubject(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] })
      closeForm()
    },
    onError: setFormError,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SubjectCreate }) => updateSubject(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] })
      closeForm()
    },
    onError: setFormError,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSubject(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subjects'] }),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const payload = toPayload(form)
    if (editingId === 'new') {
      createMutation.mutate(payload)
    } else if (editingId != null) {
      updateMutation.mutate({ id: editingId, payload })
    }
  }

  function handleDelete(subject: SubjectOut) {
    if (confirm(`Apagar "${subject.name}"? Isso também apaga atividades, faltas e notas dessa matéria.`)) {
      deleteMutation.mutate(subject.id)
    }
  }

  const saving = createMutation.isPending || updateMutation.isPending

  return (
    <div>
      <div className="page-header">
        <h1>Matérias</h1>
        {editingId === null && (
          <button type="button" className="btn-primary" onClick={startCreate}>
            <Plus size={16} />
            Nova matéria
          </button>
        )}
      </div>

      <ErrorBanner error={subjectsQuery.error} />

      {editingId !== null && (
        <form className="panel" onSubmit={handleSubmit}>
          <h2>{editingId === 'new' ? 'Nova matéria' : 'Editar matéria'}</h2>
          <label>
            Nome
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Professor
            <input value={form.professor} onChange={(e) => setForm({ ...form, professor: e.target.value })} />
          </label>
          <label>
            Dia da semana
            <select value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}>
              {DAYS_OF_WEEK.map((day) => (
                <option key={day} value={day}>
                  {day}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sala
            <input value={form.room} onChange={(e) => setForm({ ...form, room: e.target.value })} />
          </label>
          <label>
            Início
            <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
          </label>
          <label>
            Término
            <input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
          </label>
          <label>
            Semestre
            <input type="number" min={1} value={form.semestre} onChange={(e) => setForm({ ...form, semestre: e.target.value })} />
          </label>
          <label>
            Total de aulas previstas
            <input
              type="number"
              min={1}
              value={form.total_classes}
              onChange={(e) => setForm({ ...form, total_classes: e.target.value })}
            />
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
              <th>Nome</th>
              <th>Dia</th>
              <th>Horário</th>
              <th>Professor</th>
              <th>Frequência</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {subjectsQuery.data?.map((subject) => (
              <tr key={subject.id}>
                <td className="mobile-card-title">
                  <Link to={`/subjects/${subject.id}`}>{subject.name}</Link>
                </td>
                <td data-label="Dia">
                  <DayBadge day={subject.day_of_week} />
                </td>
                <td data-label="Horário">
                  {formatTime(subject.start_time)}–{formatTime(subject.end_time)}
                </td>
                <td data-label="Professor">{subject.professor ?? '—'}</td>
                <td data-label="Frequência">{attendancePercent(subject)}</td>
                <td className="row-actions">
                  <button type="button" onClick={() => startEdit(subject)}>
                    <Pencil size={14} />
                    Editar
                  </button>
                  <button type="button" onClick={() => handleDelete(subject)}>
                    <Trash2 size={14} />
                    Apagar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {subjectsQuery.data?.length === 0 && <EmptyState icon={BookOpen} message="Nenhuma matéria cadastrada ainda." />}
      </div>
    </div>
  )
}
