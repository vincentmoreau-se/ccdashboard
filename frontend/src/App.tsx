import { NavLink, Route, Routes } from "react-router-dom";

import Live from "./pages/Live";
import Overview from "./pages/Overview";
import ProjectDetail from "./pages/ProjectDetail";
import Projects from "./pages/Projects";
import Session from "./pages/Session";

export default function App() {
  return (
    <div style={{ fontFamily: "system-ui", maxWidth: 1100, margin: "0 auto", padding: 16 }}>
      <h1>CCDashboard</h1>
      <nav style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <NavLink to="/">Overview</NavLink>
        <NavLink to="/projects">Projects</NavLink>
        <NavLink to="/live">Live</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:name" element={<ProjectDetail />} />
        <Route path="/sessions/:id" element={<Session />} />
        <Route path="/live" element={<Live />} />
      </Routes>
    </div>
  );
}
