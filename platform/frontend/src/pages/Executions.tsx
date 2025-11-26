import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import { Clock, CheckCircle, XCircle, PlayCircle, AlertCircle } from 'lucide-react';

interface Execution {
  id: string;
  workflow_id: string;
  session_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
}

export default function Executions() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExecutions();
  }, []);

  const loadExecutions = async () => {
    try {
      setLoading(true);
      const data = await api.executions.list();
      setExecutions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load executions');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error':
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'running':
        return <PlayCircle className="w-5 h-5 text-blue-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      success: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
    };
    
    const colorClass = colors[status.toLowerCase() as keyof typeof colors] || 'bg-gray-100 text-gray-800';
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
        {status}
      </span>
    );
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Workflow Executions</h1>
        <p className="text-gray-600">
          View all workflow executions and their telemetry data
        </p>
      </div>

      {/* Executions Table */}
      {executions.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Executions Yet</h3>
          <p className="text-gray-600 mb-4">
            Run a workflow with CloudAuditLogger to see executions here
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Session ID</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Started</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Duration</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Error</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {executions.map((execution) => (
                <tr key={execution.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(execution.status)}
                      {getStatusBadge(execution.status)}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <code className="text-sm text-gray-600">{execution.session_id}</code>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {formatDate(execution.started_at)}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {formatDuration(execution.duration_ms)}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {execution.error_message ? (
                      <span className="text-red-600 truncate block max-w-xs" title={execution.error_message}>
                        {execution.error_message}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      to={`/executions/${execution.id}`}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stats Summary */}
      {executions.length > 0 && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Total Executions</p>
            <p className="text-2xl font-bold text-gray-900">{executions.length}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Successful</p>
            <p className="text-2xl font-bold text-green-600">
              {executions.filter(e => e.status.toLowerCase() === 'success').length}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-2xl font-bold text-red-600">
              {executions.filter(e => ['error', 'failed'].includes(e.status.toLowerCase())).length}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">Running</p>
            <p className="text-2xl font-bold text-blue-600">
              {executions.filter(e => e.status.toLowerCase() === 'running').length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}