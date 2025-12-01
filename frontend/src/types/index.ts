export interface Site {
  id: string;
  name: string;
  url: string;
  checkInterval: number;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface UptimeMetric {
  siteId: string;
  siteName: string;
  uptime: number;
  totalChecks: number;
  successfulChecks: number;
  failedChecks: number;
  avgResponseTime: number;
  lastCheckAt: string;
}

export interface ResponseTimeData {
  timestamp: string;
  responseTime: number;
  statusCode: number;
}

export interface DowntimeEvent {
  id: string;
  siteId: string;
  siteName: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  statusCode?: number;
  errorMessage?: string;
}

export interface DebugEvent {
  id: string;
  siteId: string;
  siteName: string;
  timestamp: string;
  method: string;
  url: string;
  statusCode: number;
  responseTime: number;
  requestHeaders: Record<string, string>;
  responseHeaders: Record<string, string>;
  requestBody?: string;
  responseBody?: string;
  timing: {
    dns: number;
    tcp: number;
    tls: number;
    ttfb: number;
    download: number;
    total: number;
  };
}

export interface SLAReport {
  siteId: string;
  siteName: string;
  period: string;
  uptime: number;
  availability: number;
  mttr: number;
  mtbf: number;
  incidents: number;
}

export interface FilterOptions {
  siteId?: string;
  startDate?: string;
  endDate?: string;
  statusCode?: number;
  minResponseTime?: number;
  maxResponseTime?: number;
}
