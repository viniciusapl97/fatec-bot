import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Calculator, GraduationCap, PartyPopper } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { getSubjectAttendance, getSubjectGrades, listSubjects } from '../api/resources'
import { EmptyState, ErrorBanner } from '../components/ui'

export function SubjectDetail() {
  const { id } = useParams()
  const subjectId = Number(id)

  const subjectsQuery = useQuery({ queryKey: ['subjects'], queryFn: listSubjects })
  const attendanceQuery = useQuery({ queryKey: ['subjects', subjectId, 'attendance'], queryFn: () => getSubjectAttendance(subjectId) })
  const gradesQuery = useQuery({ queryKey: ['subjects', subjectId, 'grades'], queryFn: () => getSubjectGrades(subjectId) })

  const [targetAverage, setTargetAverage] = useState('6')
  const [remainingCount, setRemainingCount] = useState('1')

  const subject = subjectsQuery.data?.find((s) => s.id === subjectId)
  const attendance = attendanceQuery.data
  const grades = gradesQuery.data?.grades ?? []

  const target = Number(targetAverage)
  const remaining = Number(remainingCount)
  const canCalculate = grades.length > 0 && Number.isFinite(target) && Number.isInteger(remaining) && remaining > 0

  let requiredScore: number | null = null
  if (canCalculate) {
    const currentSum = grades.reduce((sum, g) => sum + g.value, 0)
    requiredScore = (target * (grades.length + remaining) - currentSum) / remaining
  }

  return (
    <div>
      <Link className="back-link" to="/subjects">
        <ArrowLeft size={14} />
        Matérias
      </Link>
      <div className="page-header">
        <h1>{subject?.name ?? gradesQuery.data?.subject_name ?? 'Matéria'}</h1>
      </div>

      <section className="panel-surface">
        <h2>Frequência</h2>
        <ErrorBanner error={attendanceQuery.error} />
        {attendance && (
          <ul className="plain-list">
            <li>
              <span className="stat-key">Aulas previstas</span>
              <span className="stat-val">{attendance.total_classes ?? 'não informado'}</span>
            </li>
            <li>
              <span className="stat-key">Faltas</span>
              <span className="stat-val">{attendance.total_absences}</span>
            </li>
            <li>
              <span className="stat-key">Frequência</span>
              <span className="stat-val">{attendance.percent != null ? `${attendance.percent.toFixed(1)}%` : '—'}</span>
            </li>
            <li>
              <span className="stat-key">Faltas restantes permitidas</span>
              <span className="stat-val">{attendance.remaining_allowed ?? '—'}</span>
            </li>
            {attendance.failed && (
              <li>
                <span className="stat-key danger-text">Reprovado por falta.</span>
              </li>
            )}
            {!attendance.failed && attendance.at_risk && (
              <li>
                <span className="stat-key warning">Em risco de reprovação por falta.</span>
              </li>
            )}
          </ul>
        )}
      </section>

      <section className="panel-surface">
        <h2>Notas</h2>
        <ErrorBanner error={gradesQuery.error} />
        <ul className="plain-list">
          {grades.map((grade) => (
            <li key={grade.id}>
              <span className="stat-key">{grade.name}</span>
              <span className="stat-val">{grade.value}</span>
            </li>
          ))}
          {gradesQuery.data?.average != null && (
            <li>
              <span className="stat-key">Média</span>
              <span className="stat-val">{gradesQuery.data.average}</span>
            </li>
          )}
        </ul>
        {grades.length === 0 && <EmptyState className="empty-state" icon={GraduationCap} message="Nenhuma nota lançada ainda." />}

        {grades.length > 0 && (
          <div className="calculator">
            <h3>
              <Calculator size={14} />
              Quanto preciso tirar?
            </h3>
            <div className="calculator-grid">
              <label>
                Média desejada
                <input type="number" step="0.1" min={0} value={targetAverage} onChange={(e) => setTargetAverage(e.target.value)} />
              </label>
              <label>
                Notas que faltam
                <input type="number" min={1} step={1} value={remainingCount} onChange={(e) => setRemainingCount(e.target.value)} />
              </label>
            </div>

            {requiredScore != null && (
              <p className={`calculator-result ${requiredScore <= 0 ? 'success' : requiredScore > 10 ? 'warning' : ''}`}>
                {requiredScore <= 0 ? (
                  <>
                    <PartyPopper size={16} />
                    Você já garante média {target} só com as notas atuais.
                  </>
                ) : (
                  <>
                    Você precisa de <strong>{requiredScore.toFixed(1)}</strong> de média{' '}
                    {remaining > 1 ? `nas próximas ${remaining} notas` : 'na próxima nota'} pra fechar com {target}.
                    {requiredScore > 10 && ' Pode não ser alcançável.'}
                  </>
                )}
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
