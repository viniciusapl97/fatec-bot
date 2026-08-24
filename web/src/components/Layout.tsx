import { BookOpen, CalendarX2, ClipboardList, GraduationCap, Home, LogOut } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Início', end: true, icon: Home },
  { to: '/subjects', label: 'Matérias', icon: BookOpen },
  { to: '/activities', label: 'Atividades', icon: ClipboardList },
  { to: '/absences', label: 'Faltas', icon: CalendarX2 },
  { to: '/grades', label: 'Notas', icon: GraduationCap },
]

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand">
          <span className="brand-mark" />
          Jovis
        </div>

        <nav className="app-nav">
          {NAV_ITEMS.map(({ to, label, end, icon: Icon }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? 'active' : '')}>
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="app-user">
          <div className="app-user-avatar">{user?.first_name?.[0]?.toUpperCase()}</div>
          <div className="app-user-info">
            <span className="app-user-name">{user?.first_name}</span>
            {user?.username && <span className="app-user-handle">@{user.username}</span>}
          </div>
          <button type="button" className="icon-button" onClick={handleLogout} title="Sair">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <header className="mobile-topbar">
        <div className="brand">
          <span className="brand-mark" />
          Jovis
        </div>
        <div className="mobile-topbar-right">
          <div className="app-user-avatar">{user?.first_name?.[0]?.toUpperCase()}</div>
          <button type="button" className="icon-button" onClick={handleLogout} title="Sair">
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="mobile-tabbar">
        {NAV_ITEMS.map(({ to, label, end, icon: Icon }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? 'active' : '')}>
            <Icon size={20} strokeWidth={2} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
