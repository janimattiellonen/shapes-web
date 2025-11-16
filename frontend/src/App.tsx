import './App.css'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { ShapeDetector } from './components/ShapeDetector'
import { BorderDetection } from './components/BorderDetection'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="main-nav">
          <Link to="/" className="nav-link">Shape Detection</Link>
          <Link to="/discs/border-detection" className="nav-link">Disc Border Detection</Link>
          <a href="http://localhost:8000/docs" className="nav-link" target="_blank" rel="noopener noreferrer">API Docs</a>
        </nav>

        <Routes>
          <Route path="/" element={<ShapeDetector />} />
          <Route path="/discs/border-detection" element={<BorderDetection />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
