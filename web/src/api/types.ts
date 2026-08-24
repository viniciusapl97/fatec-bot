// Espelha api/schemas.py — mesmo contrato que a API expõe, não os models
// do bot diretamente (ver bot/db/models.py vs api/schemas.py).

export type DayOfWeek =
  | 'Segunda'
  | 'Terça'
  | 'Quarta'
  | 'Quinta'
  | 'Sexta'
  | 'Sábado'

export const DAYS_OF_WEEK: DayOfWeek[] = [
  'Segunda',
  'Terça',
  'Quarta',
  'Quinta',
  'Sexta',
  'Sábado',
]

export type ActivityType = 'trabalho' | 'prova'

export interface UserOut {
  user_id: number
  first_name: string
  username: string | null
  notifications_enabled: boolean
  notification_hour: number
}

export interface SubjectOut {
  id: number
  name: string
  professor: string | null
  day_of_week: string
  room: string | null
  start_time: string | null // "HH:MM:SS"
  end_time: string | null
  semestre: number | null
  total_classes: number | null
  total_absences: number
  percent: number | null
  remaining_allowed: number | null
  at_risk: boolean
  failed: boolean
}

export interface ActivityOut {
  id: number
  activity_type: string
  name: string
  due_date: string // "YYYY-MM-DD"
  notes: string | null
  subject_id: number
  subject_name: string
}

export interface AbsenceOut {
  id: number
  absence_date: string
  quantity: number
  notes: string | null
  subject_id: number
  subject_name: string
}

export interface GradeOut {
  id: number
  name: string
  value: number
  subject_id: number
  subject_name: string
}

export interface AttendanceOut {
  subject_id: number
  total_classes: number | null
  total_absences: number
  percent: number | null
  remaining_allowed: number | null
  at_risk: boolean
  failed: boolean
}

export interface SubjectGradesOut {
  subject_id: number
  subject_name: string
  grades: GradeOut[]
  average: number | null
}

export interface SubjectCreate {
  name: string
  professor?: string | null
  day_of_week: DayOfWeek
  room?: string | null
  start_time?: string | null
  end_time?: string | null
  semestre?: number | null
  total_classes?: number | null
}

export type SubjectUpdate = Partial<SubjectCreate>

export interface ActivityCreate {
  subject_id: number
  activity_type: ActivityType
  name: string
  due_date: string
  notes?: string | null
}

export interface ActivityUpdate {
  subject_id?: number
  name?: string
  due_date?: string
  notes?: string | null
}

export interface AbsenceCreate {
  subject_id: number
  absence_date: string
  quantity: number
  notes?: string | null
}

export interface AbsenceUpdate {
  quantity: number
}

export interface GradeCreate {
  subject_id: number
  name: string
  value: number
}

export interface GradeUpdate {
  name: string
  value: number
}

export interface TelegramLoginPayload {
  id: number
  first_name: string
  last_name?: string | null
  username?: string | null
  photo_url?: string | null
  auth_date: number
  hash: string
}

export interface AccessTokenOut {
  access_token: string
  token_type: string
}
