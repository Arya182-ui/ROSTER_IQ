import React, { useState } from "react";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import MainLayout from "./layout/MainLayout";
import DashboardPage from "./pages/DashboardPage";
import InvestigationsPage from "./pages/InvestigationsPage";

const ROUTE_META = {
  "/dashboard": {
    view: "dashboard",
    title: "AI Operations Dashboard",
    subtitle: "Live pipeline health, market drift, and structured operational reporting."
  },
  "/investigations": {
    view: "investigations",
    title: "Investigation History",
    subtitle: "Recent investigations, saved outcomes, and quick reruns for follow-up analysis."
  },
  "/chat": {
    view: "chat",
    title: "Agent Chat",
    subtitle: "Ask RosterIQ for triage guidance, market context, and root-cause analysis."
  }
};

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const [queuedQuery, setQueuedQuery] = useState("");

  const currentPath = location.pathname === "/" ? "/dashboard" : location.pathname;
  const meta = ROUTE_META[currentPath] || ROUTE_META["/dashboard"];

  function handleRerun(query) {
    setQueuedQuery(query);
    navigate("/chat");
  }

  return (
    <MainLayout
      activeView={meta.view}
      title={meta.title}
      subtitle={meta.subtitle}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage onOpenChat={() => navigate("/chat")} />} />
        <Route
          path="/investigations"
          element={<InvestigationsPage mode="investigations" onRerun={handleRerun} />}
        />
        <Route
          path="/chat"
          element={
            <InvestigationsPage
              mode="chat"
              queuedQuery={queuedQuery}
              onQueuedQueryConsumed={() => setQueuedQuery("")}
            />
          }
        />
      </Routes>
    </MainLayout>
  );
}
