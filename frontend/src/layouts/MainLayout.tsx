import { Outlet, Link } from 'react-router-dom'

export function MainLayout() {
  return (
    <div className="app">
      <nav className="main-nav">
        <Link to="/" className="nav-link">Registered Discs</Link>
        <Link to="/discs/new" className="nav-link">Add New Disc</Link>
        <Link to="/discs/shape-detection" className="nav-link">Shape Detection</Link>
        <Link to="/discs/border-detection" className="nav-link">Disc Border Detection</Link>
        <a
          href="http://localhost:8000/docs"
          className="nav-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          API Docs
        </a>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
