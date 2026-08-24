// Uma função por endpoint da API (api/routers/*.py) — nenhuma regra de
// negócio aqui, só o mapeamento de chamada HTTP.

import { api } from './client'
import type {
  AbsenceCreate,
  AbsenceOut,
  AbsenceUpdate,
  AccessTokenOut,
  ActivityCreate,
  ActivityOut,
  ActivityType,
  ActivityUpdate,
  AttendanceOut,
  GradeCreate,
  GradeOut,
  GradeUpdate,
  SubjectCreate,
  SubjectGradesOut,
  SubjectOut,
  SubjectUpdate,
  TelegramLoginPayload,
  UserOut,
} from './types'

// --- auth ---
export const loginWithTelegram = (payload: TelegramLoginPayload) =>
  api.post<AccessTokenOut>('/auth/telegram', payload)

// --- me ---
export const getMe = () => api.get<UserOut>('/me')

// --- subjects ---
export const listSubjects = () => api.get<SubjectOut[]>('/subjects')
export const createSubject = (payload: SubjectCreate) => api.post<SubjectOut>('/subjects', payload)
export const updateSubject = (id: number, payload: SubjectUpdate) => api.patch<SubjectOut>(`/subjects/${id}`, payload)
export const deleteSubject = (id: number) => api.delete<void>(`/subjects/${id}`)
export const getSubjectAttendance = (id: number) => api.get<AttendanceOut>(`/subjects/${id}/attendance`)
export const getSubjectGrades = (id: number) => api.get<SubjectGradesOut>(`/subjects/${id}/grades`)

// --- activities ---
export const listActivities = (activityType?: ActivityType) =>
  api.get<ActivityOut[]>(`/activities${activityType ? `?activity_type=${activityType}` : ''}`)
export const createActivity = (payload: ActivityCreate) => api.post<ActivityOut>('/activities', payload)
export const updateActivity = (id: number, payload: ActivityUpdate) => api.patch<ActivityOut>(`/activities/${id}`, payload)
export const deleteActivity = (id: number) => api.delete<void>(`/activities/${id}`)

// --- absences ---
export const listAbsences = () => api.get<AbsenceOut[]>('/absences')
export const createAbsence = (payload: AbsenceCreate) => api.post<AbsenceOut>('/absences', payload)
export const updateAbsence = (id: number, payload: AbsenceUpdate) => api.patch<AbsenceOut>(`/absences/${id}`, payload)
export const deleteAbsence = (id: number) => api.delete<void>(`/absences/${id}`)

// --- grades ---
export const listGrades = () => api.get<GradeOut[]>('/grades')
export const createGrade = (payload: GradeCreate) => api.post<GradeOut>('/grades', payload)
export const updateGrade = (id: number, payload: GradeUpdate) => api.patch<GradeOut>(`/grades/${id}`, payload)
export const deleteGrade = (id: number) => api.delete<void>(`/grades/${id}`)
