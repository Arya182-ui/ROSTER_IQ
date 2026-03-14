import axios from "axios";
import { APP_CONFIG } from "../config";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: APP_CONFIG.apiTimeout || 30000
});

async function getJson(path, config = {}) {
  const response = await client.get(path, config);
  return response.data;
}

async function postJson(path, payload) {
  const response = await client.post(path, payload);
  return response.data;
}

export function askAgent(query) {
  return postJson("/ask", { query });
}

export function getPipelineHealth() {
  return getJson("/analytics/pipeline-health");
}

export function getMarketTrend() {
  return getJson("/analytics/market-trend");
}

export function getRecordQuality() {
  return getJson("/analytics/record-quality");
}

export function getRetryAnalysis() {
  return getJson("/analytics/retry-analysis");
}

export function getRootCause(state) {
  return getJson(`/analytics/root-cause/${state}`);
}

export function getPipelineReport(state, organization) {
  const params = {};
  if (state) {
    params.state = state;
  }
  if (organization) {
    params.organization = organization;
  }
  return getJson("/analytics/pipeline-report", { params });
}

export function getStuckRos() {
  return getJson("/stuck-ros");
}

export function getFailedRos() {
  return getJson("/failed-ros");
}

export function getDurationAnomalies() {
  return getJson("/duration-anomalies");
}

export function getInvestigationHistory(limit = 12) {
  return getJson("/investigations/history", { params: { limit } });
}

export function getHealth() {
  return getJson("/health");
}
