import type { CSSProperties } from "react";
import { NavLink, Route, Routes } from "react-router-dom";

import Insights from "./pages/Insights";
import Live from "./pages/Live";
import Overview from "./pages/Overview";
import ProjectDetail from "./pages/ProjectDetail";
import Projects from "./pages/Projects";
import Session from "./pages/Session";
import TechTooling from "./pages/TechTooling";
import { theme } from "./theme";

const navLinkStyle = ({ isActive }: { isActive: boolean }): CSSProperties => ({
  padding: "6px 2px",
  fontSize: 14,
  fontWeight: isActive ? 600 : 500,
  color: isActive ? theme.colors.text : theme.colors.textMuted,
  borderBottom: `2px solid ${isActive ? theme.colors.accent : "transparent"}`,
  transition: "color 0.15s ease, border-color 0.15s ease",
});

export default function App() {
  return (
    <div style={{ fontFamily: theme.font.body, minHeight: "100vh" }}>
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          backdropFilter: "blur(12px)",
          background: "rgba(22, 20, 15, 0.72)",
          borderBottom: `1px solid ${theme.colors.border}`,
        }}
      >
        <div
          style={{
            maxWidth: 1100,
            margin: "0 auto",
            padding: "14px 16px",
            display: "flex",
            alignItems: "center",
            gap: 28,
          }}
        >
          <NavLink to="/" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              aria-hidden
              style={{
                width: 12,
                height: 12,
                borderRadius: 4,
                background: theme.colors.accent,
                boxShadow: `0 0 14px ${theme.colors.accent}`,
                transform: "rotate(45deg)",
              }}
            />
            <h1
              style={{
                margin: 0,
                fontFamily: theme.font.display,
                fontSize: 19,
                fontWeight: 600,
                color: theme.colors.text,
                letterSpacing: "-0.01em",
              }}
            >
              CCDashboard
            </h1>
          </NavLink>
          <nav style={{ display: "flex", gap: 22, marginLeft: 8 }}>
            <NavLink to="/" end style={navLinkStyle}>Overview</NavLink>
            <NavLink to="/insights" style={navLinkStyle}>Insights</NavLink>
            <NavLink to="/projects" style={navLinkStyle}>Projects</NavLink>
            <NavLink to="/tech" style={navLinkStyle}>Tech & Tooling</NavLink>
            <NavLink to="/live" style={navLinkStyle}>Live</NavLink>
          </nav>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "8px 16px 64px" }}>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:name" element={<ProjectDetail />} />
          <Route path="/sessions/:id" element={<Session />} />
          <Route path="/tech" element={<TechTooling />} />
          <Route path="/live" element={<Live />} />
        </Routes>
      </main>
    </div>
  );
}
