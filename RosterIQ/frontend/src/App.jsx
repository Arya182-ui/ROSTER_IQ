import React, { useState } from "react";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import MainLayout from "./layout/MainLayout";
import DashboardPage from "./pages/DashboardPage";
import InvestigationsPage from "./pages/InvestigationsPage";
import AgentChatPage from "./pages/AgentChatPage";

const ROUTE_META = {
  "/dashboard": {
    view: "dashboard",
    title: "AI Operations Dashboard",
    subtitle: "Live pipeline health, market drift, and structured operational reporting."
  },
  "/investigations": {
    view: "investigations",
    title: "Investigation Library",
    subtitle: "Saved investigation outcomes, operational context, and one-click reruns back into chat."
  },
  "/chat": {
    view: "chat",
    title: "AI Triage Copilot",
    subtitle: "Ask in plain language. RosterIQ routes the request, summarizes the answer, and keeps the workflow moving."
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
    <MainLayout activeView={meta.view} title={meta.title} subtitle={meta.subtitle}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage onOpenChat={() => navigate("/chat")} />} />
        <Route
          path="/investigations"
          element={<InvestigationsPage onOpenChat={() => navigate("/chat")} onRerun={handleRerun} />}
        />
        <Route
          path="/chat"
          element={
            <AgentChatPage
              queuedQuery={queuedQuery}
              onQueuedQueryConsumed={() => setQueuedQuery("")}
              onOpenInvestigations={() => navigate("/investigations")}
            />
          }
        />
      </Routes>
    </MainLayout>
  );
}
