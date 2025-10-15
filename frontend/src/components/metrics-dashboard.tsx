"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/loading-spinner'

interface ParseMetrics {
  total_parses: number
  successful_parses: number
  failed_parses: number
  success_rate_percent: number
  failure_rate_percent: number
  average_duration_ms: number
  average_sections_per_parse: number
  average_skills_per_parse: number
  total_warnings: number
}

interface MetricsData {
  status: string
  time_window_hours: number
  metrics: ParseMetrics
}

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeWindow, setTimeWindow] = useState(24)

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`http://localhost:8000/api/metrics/parsing?hours=${timeWindow}`)
      const data = await response.json()

      if (data.status === 'error') {
        setError(data.error)
      } else {
        setMetrics(data)
      }
    } catch (err) {
      setError('Failed to fetch metrics')
      console.error('Metrics fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
  }, [timeWindow])

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <LoadingSpinner message="Loading metrics..." />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchMetrics}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!metrics) {
    return null
  }

  const { metrics: data } = metrics

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">SCOUT Metrics</h2>
        <div className="flex items-center gap-2">
          <label htmlFor="timeWindow" className="text-sm font-medium">Time Window:</label>
          <select
            id="timeWindow"
            value={timeWindow}
            onChange={(e) => setTimeWindow(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value={1}>1 Hour</option>
            <option value={6}>6 Hours</option>
            <option value={24}>24 Hours</option>
            <option value={72}>3 Days</option>
            <option value={168}>1 Week</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Parses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_parses}</div>
            <p className="text-xs text-gray-600 mt-1">
              {data.successful_parses} successful, {data.failed_parses} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {data.success_rate_percent.toFixed(1)}%
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={data.success_rate_percent > 90 ? "success" : data.success_rate_percent > 75 ? "warning" : "destructive"}>
                {data.success_rate_percent > 90 ? "Excellent" : data.success_rate_percent > 75 ? "Good" : "Needs Attention"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.average_duration_ms.toFixed(0)}ms
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={data.average_duration_ms < 3000 ? "success" : data.average_duration_ms < 8000 ? "warning" : "destructive"}>
                {data.average_duration_ms < 3000 ? "Fast" : data.average_duration_ms < 8000 ? "Moderate" : "Slow"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{data.total_warnings}</div>
            <p className="text-xs text-gray-600 mt-1">
              Quality indicators
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Extraction Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Avg Sections per Parse</span>
                <span className="text-lg font-bold">{data.average_sections_per_parse.toFixed(1)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Avg Skills per Parse</span>
                <span className="text-lg font-bold">{data.average_skills_per_parse.toFixed(1)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Warning Rate</span>
                <span className="text-lg font-bold text-yellow-600">
                  {data.total_parses > 0 ? ((data.total_warnings / data.total_parses) * 100).toFixed(1) : 0}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quality Indicators</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">System Health</span>
                <Badge variant={data.success_rate_percent > 90 ? "success" : "warning"}>
                  {data.success_rate_percent > 90 ? "Healthy" : "Monitoring"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Performance</span>
                <Badge variant={data.average_duration_ms < 5000 ? "success" : "warning"}>
                  {data.average_duration_ms < 5000 ? "Optimal" : "Review"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Data Quality</span>
                <Badge variant={data.average_sections_per_parse > 3 ? "success" : "warning"}>
                  {data.average_sections_per_parse > 3 ? "Good" : "Monitor"}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Time Window: {timeWindow} {timeWindow === 1 ? 'Hour' : 'Hours'}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Metrics are collected in real-time during parsing operations.
            Higher success rates and lower processing times indicate optimal system performance.
            Warnings help identify content extraction challenges and guide format recommendations.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}