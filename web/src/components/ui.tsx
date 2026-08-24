import type { LucideIcon } from 'lucide-react'
import { ApiError } from '../api/client'
import type { ActivityType, DayOfWeek } from '../api/types'

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Erro inesperado.'
}

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null
  return <p className="error-banner">{errorMessage(error)}</p>
}

export function EmptyState({ icon: Icon, message, className = 'empty-note' }: { icon: LucideIcon; message: string; className?: string }) {
  return (
    <p className={className}>
      <Icon size={16} strokeWidth={2} />
      {message}
    </p>
  )
}

// "HH:MM:SS" (vindo da API) -> "HH:MM" (exibição)
export function formatTime(value: string | null): string {
  return value ? value.slice(0, 5) : '—'
}

// "YYYY-MM-DD" -> "DD/MM/YYYY"
export function formatDate(value: string): string {
  const [year, month, day] = value.split('-')
  return `${day}/${month}/${year}`
}

export function DayBadge({ day }: { day: string }) {
  return <span className="badge badge-day">{day}</span>
}

export function ActivityTypeBadge({ type }: { type: ActivityType | string }) {
  return <span className={`badge badge-type-${type}`}>{type === 'trabalho' ? 'Trabalho' : 'Prova'}</span>
}

const DAY_OF_WEEK_BY_JS_DAY: Record<number, DayOfWeek> = {
  1: 'Segunda',
  2: 'Terça',
  3: 'Quarta',
  4: 'Quinta',
  5: 'Sexta',
  6: 'Sábado',
}

const WEEKDAY_LONG = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado']

const MONTH_NAMES = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
]

// "YYYY-MM-DD" na data local (não UTC) — para comparar com Subject.day_of_week
// e Activity.due_date, que são datas simples sem fuso.
export function todayIso(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

export function todayDayOfWeek(): DayOfWeek | null {
  return DAY_OF_WEEK_BY_JS_DAY[new Date().getDay()] ?? null
}

export function todayLabel(): string {
  const now = new Date()
  const weekday = WEEKDAY_LONG[now.getDay()]
  return `${weekday.charAt(0).toUpperCase()}${weekday.slice(1)}, ${now.getDate()} de ${MONTH_NAMES[now.getMonth()]}`
}
