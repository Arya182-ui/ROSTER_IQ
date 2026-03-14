import React from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";

export default function MainLayout({ activeView, title, subtitle, children }) {
  return (
    <div className="min-h-screen px-4 py-4 lg:px-6 lg:py-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-[1600px] gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
        <Sidebar />
        <main className="min-w-0 flex flex-col gap-6">
          <Header title={title} subtitle={subtitle} activeView={activeView} />
          <div>{children}</div>
        </main>
      </div>
    </div>
  );
}
