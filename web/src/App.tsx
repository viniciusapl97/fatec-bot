import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { Absences } from './pages/Absences'
import { Activities } from './pages/Activities'
import { Dashboard } from './pages/Dashboard'
import { Grades } from './pages/Grades'
import { Login } from './pages/Login'
import { SubjectDetail } from './pages/SubjectDetail'
import { Subjects } from './pages/Subjects'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="subjects" element={<Subjects />} />
        <Route path="subjects/:id" element={<SubjectDetail />} />
        <Route path="activities" element={<Activities />} />
        <Route path="absences" element={<Absences />} />
        <Route path="grades" element={<Grades />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
