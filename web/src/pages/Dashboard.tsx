import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, BookOpen, CalendarClock, ClipboardCheck, ClipboardList, Coffee, ShieldAlert, TrendingUp, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { listActivities, listSubjects } from '../api/resources'
import { useAuth } from '../auth/AuthContext'
import { EmptyState, ErrorBanner, formatDate, formatTime, todayDayOfWeek, todayIso, todayLabel } from '../components/ui'
import type { SubjectOut } from '../api/types'

const DISMISSED_RISKS_KEY = 'jovis_dismissed_risks'

// Guarda o estado de risco (não falso "dismissed: true") no momento em que o
// usuário fechou o aviso — se a falta piorar depois (menos faltas restantes,
// ou vira reprovação), o snapshot não bate mais e o aviso volta a aparecer.
type RiskSnapshot = Record<number, { remaining_allowed: number | null; failed: boolean }>

function readDismissedRisks(): RiskSnapshot {
  try {
    return JSON.parse(localStorage.getItem(DISMISSED_RISKS_KEY) ?? '{}')
  } catch {
    return {}
  }
}

export function Dashboard() {
  const { user } = useAuth()
  const subjectsQuery = useQuery({ queryKey: ['subjects'], queryFn: listSubjects })
  const activitiesQuery = useQuery({ queryKey: ['activities'], queryFn: () => listActivities() })
  const [dismissedRisks, setDismissedRisks] = useState<RiskSnapshot>(readDismissedRisks)

  function dismissRisk(subject: SubjectOut) {
    const next = { ...dismissedRisks, [subject.id]: { remaining_allowed: subject.remaining_allowed, failed: subject.failed } }
    setDismissedRisks(next)
    localStorage.setItem(DISMISSED_RISKS_KEY, JSON.stringify(next))
  }

  const today = todayDayOfWeek()
  const todayIsoStr = todayIso()

  const todaySubjects = [...(subjectsQuery.data ?? [])]
    .filter((s) => s.day_of_week === today)
    .sort((a, b) => (a.start_time ?? '').localeCompare(b.start_time ?? ''))

  const todayActivities = (activitiesQuery.data ?? []).filter((a) => a.due_date === todayIsoStr)

  const upcoming = [...(activitiesQuery.data ?? [])]
    .filter((a) => a.due_date >= todayIsoStr)
    .sort((a, b) => a.due_date.localeCompare(b.due_date))
    .slice(0, 5)

  const withAttendance = (subjectsQuery.data ?? []).filter((s) => s.percent != null)
  const avgAttendance = withAttendance.length
    ? Math.round(withAttendance.reduce((sum, s) => sum + s.percent!, 0) / withAttendance.length)
    : null

  const riskySubjects = (subjectsQuery.data ?? []).filter((s) => {
    if (!s.at_risk && !s.failed) return false
    const dismissed = dismissedRisks[s.id]
    return !(dismissed && dismissed.remaining_allowed === s.remaining_allowed && dismissed.failed === s.failed)
  })

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <p className="eyebrow">{todayLabel()}</p>
        <h1>Olá, {user?.first_name}</h1>
      </div>

      {riskySubjects.length > 0 && (
        <section className="risk-banner">
          <ShieldAlert size={18} />
          <div>
            <strong>Atenção à frequência</strong>
            <ul>
              {riskySubjects.map((subject) => (
                <li key={subject.id} className={subject.failed ? 'failed' : undefined}>
                  <span>
                    <Link to={`/subjects/${subject.id}`}>{subject.name}</Link>
                    {subject.failed
                      ? ' — reprovado por falta'
                      : ` — só ${subject.remaining_allowed} falta${subject.remaining_allowed === 1 ? '' : 's'} restante${subject.remaining_allowed === 1 ? '' : 's'}`}
                  </span>
                  <button type="button" className="icon-button" onClick={() => dismissRisk(subject)} title="Dispensar aviso">
                    <X size={14} />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <section className="panel-surface">
        <div className="today-panel-header">
          <CalendarClock size={18} />
          <h2>Hoje</h2>
        </div>

        <ErrorBanner error={subjectsQuery.error ?? activitiesQuery.error} />

        <div className="today-columns">
          <div>
            <h3>Aulas</h3>
            {todaySubjects.length === 0 ? (
              <EmptyState className="empty-state" icon={Coffee} message="Nenhuma aula hoje." />
            ) : (
              <ul className="today-list">
                {todaySubjects.map((subject) => (
                  <li key={subject.id} className="schedule-row">
                    <span className="schedule-time">
                      {formatTime(subject.start_time)}–{formatTime(subject.end_time)}
                    </span>
                    <div className="schedule-info">
                      <strong>{subject.name}</strong>
                      {subject.room && <span>Sala {subject.room}</span>}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <h3>Atividades e provas</h3>
            {todayActivities.length === 0 ? (
              <EmptyState className="empty-state" icon={ClipboardCheck} message="Nada previsto pra hoje." />
            ) : (
              <ul className="today-list">
                {todayActivities.map((activity) => (
                  <li key={activity.id} className="deadline-row">
                    <AlertTriangle size={16} />
                    <div className="deadline-info">
                      <strong>{activity.name}</strong>
                      <span>
                        {activity.subject_name} · {activity.activity_type === 'trabalho' ? 'Trabalho' : 'Prova'}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      <section className="stat-grid">
        <Link className="stat-card" to="/subjects">
          <BookOpen size={18} className="stat-icon" />
          <span className="stat-value">{subjectsQuery.data?.length ?? '—'}</span>
          <span className="stat-label">Matérias</span>
        </Link>
        <Link className="stat-card" to="/activities">
          <ClipboardList size={18} className="stat-icon" />
          <span className="stat-value">{activitiesQuery.data?.length ?? '—'}</span>
          <span className="stat-label">Trabalhos e provas</span>
        </Link>
        <div className="stat-card">
          <TrendingUp size={18} className="stat-icon" />
          <span className="stat-value">{avgAttendance != null ? `${avgAttendance}%` : '—'}</span>
          <span className="stat-label">Frequência média</span>
        </div>
      </section>

      <section className="panel-surface">
        <h2>Próximos prazos</h2>
        {upcoming.length === 0 ? (
          <EmptyState className="empty-state" icon={ClipboardCheck} message="Nenhum trabalho ou prova cadastrado." />
        ) : (
          <ul className="plain-list">
            {upcoming.map((activity) => (
              <li key={activity.id}>
                <span className="stat-key">
                  {activity.name} — {activity.subject_name}
                </span>
                <span className="stat-val">{formatDate(activity.due_date)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
