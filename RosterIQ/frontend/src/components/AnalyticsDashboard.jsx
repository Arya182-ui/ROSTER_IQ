import React from "react";
import MarketTrendChart from "./MarketTrendChart";
import PipelineHealthChart from "./PipelineHealthChart";
import RecordQualityChart from "./RecordQualityChart";
import RetryAnalysisChart from "./RetryAnalysisChart";

export default function AnalyticsDashboard({ pipelineHealth, marketTrend, retryAnalysis, recordQuality, failedRos, focusState }) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <PipelineHealthChart stageHealth={pipelineHealth} failedRos={failedRos} focusState={focusState} />
      <MarketTrendChart data={marketTrend} />
      <RetryAnalysisChart data={retryAnalysis} />
      <RecordQualityChart data={recordQuality} />
    </div>
  );
}
