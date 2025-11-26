import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  PlayCircle, 
  AlertCircle,
  ArrowLeft,
  Activity,
  Database,
  Zap,
  Filter,
  Search
} from 'lucide-react';

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

interface NodeExecution {
  id: string;
  node_id: string;
  node_name: string;
  node_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  prep_duration_ms: number | null;
  exec_duration_ms: number | null;
  post_duration_ms: number | null;
  error_message: string | null;
  retry_count: number;
}

interface TelemetryEvent {
  id: string;
  event_type: string;
  timestamp: string;
  data: any;
}

interface TelemetrySpan {
  id: string;
  span_id: string;
  trace_id: string;
  name: string;
  kind: string;
  status: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  attributes: any;
}

export default function ExecutionDetail() {
  const { executionId } = useParams<{ executionId: string }>();
  const [execution, setExecution] = useState<Execution | null>(null);
  const [nodeExecutions, setNodeExecutions] = useState<NodeExecution[]>([]);
  const [telemetryEvents, setTelemetryEvents] = useState<TelemetryEvent[]>([]);
  const [telemetrySpans, setTelemetrySpans] = useState<TelemetrySpan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'nodes' | 'events' | 'spans'>('nodes');

  // Filters for telemetry events
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [nodeNameFilter, setNodeNameFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    if (executionId) {
      loadExecutionData();
    }
  }, [executionId]);

  const loadExecutionData = async () => {
    try {
      setLoading(true);
      const [execData, nodesData, eventsResponse, spansResponse] = await Promise.all([
        api.executions.get(executionId!),
        api.executions.getNodes(executionId!),
        api.executions.getTelemetryEvents(executionId!),
        api.executions.getTelemetrySpans(executionId!)
      ]);
      
      setExecution(execData);
      setNodeExecutions(nodesData);
      setTelemetryEvents(eventsResponse.events || eventsResponse);
      setTelemetrySpans(spansResponse.spans || spansResponse);
    } catch (err: any) {
      setError(err.message || 'Failed to load execution data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return <CheckCircle className="w-6 h-6 text-green-600" />;
      case 'error':
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-600" />;
      case 'running':
        return <PlayCircle className="w-6 h-6 text-blue-600" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-600" />;
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
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass}`}>
        {status}
      </span>
    );
  };

  const formatDuration = (ms: number | null) => {
    if (!ms && ms !== 0) return '-';
    if (ms < 1) return `${(ms * 1000).toFixed(2)}μs`;
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Extract node name from event data
  const getNodeNameFromEvent = (event: TelemetryEvent): string => {
    return event.data?.node_name || event.data?.name || '-';
  };

  // Get unique event types for filter
  const uniqueEventTypes = ['all', ...new Set(telemetryEvents.map(e => e.event_type))];

  // Get unique node names for filter
  const uniqueNodeNames = ['all', ...new Set(
    telemetryEvents
      .map(e => getNodeNameFromEvent(e))
      .filter(name => name !== '-')
  )];

  // Filter telemetry events
  const filteredEvents = telemetryEvents.filter(event => {
    const nodeName = getNodeNameFromEvent(event);
    
    // Event type filter
    if (eventTypeFilter !== 'all' && event.event_type !== eventTypeFilter) {
      return false;
    }
    
    // Node name filter
    if (nodeNameFilter !== 'all' && nodeName !== nodeNameFilter) {
      return false;
    }
    
    // Search query
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const eventJson = JSON.stringify(event.data).toLowerCase();
      return (
        event.event_type.toLowerCase().includes(searchLower) ||
        nodeName.toLowerCase().includes(searchLower) ||
        eventJson.includes(searchLower)
      );
    }
    
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading execution data...</p>
        </div>
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="max-w-7xl mx-auto p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error || 'Execution not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      {/* Back Button */}
      <Link 
        to="/executions" 
        className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-6"
      >
        <ArrowLeft size={20} />
        Back to Executions
      </Link>

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            {getStatusIcon(execution.status)}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Execution Details</h1>
              <p className="text-sm text-gray-600 mt-1">
                Session: <code className="bg-gray-100 px-2 py-1 rounded">{execution.session_id}</code>
              </p>
            </div>
          </div>
          {getStatusBadge(execution.status)}
        </div>

        {/* Execution Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="border-l-4 border-blue-500 pl-4">
            <p className="text-sm text-gray-600">Started At</p>
            <p className="text-lg font-semibold text-gray-900">{formatDate(execution.started_at)}</p>
          </div>
          <div className="border-l-4 border-green-500 pl-4">
            <p className="text-sm text-gray-600">Duration</p>
            <p className="text-lg font-semibold text-gray-900">{formatDuration(execution.duration_ms)}</p>
          </div>
          <div className="border-l-4 border-purple-500 pl-4">
            <p className="text-sm text-gray-600">Nodes Executed</p>
            <p className="text-lg font-semibold text-gray-900">{nodeExecutions.length}</p>
          </div>
          <div className="border-l-4 border-orange-500 pl-4">
            <p className="text-sm text-gray-600">Telemetry Events</p>
            <p className="text-lg font-semibold text-gray-900">{telemetryEvents.length}</p>
          </div>
        </div>

        {/* Error Message */}
        {execution.error_message && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-red-900 mb-1">Error Message:</p>
            <p className="text-sm text-red-800 font-mono">{execution.error_message}</p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 px-6">
            <button
              onClick={() => setActiveTab('nodes')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition ${
                activeTab === 'nodes'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <Activity size={18} />
                Node Executions ({nodeExecutions.length})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('events')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition ${
                activeTab === 'events'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <Database size={18} />
                Telemetry Events ({filteredEvents.length}/{telemetryEvents.length})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('spans')}
              className={`py-4 px-2 border-b-2 font-medium text-sm transition ${
                activeTab === 'spans'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <Zap size={18} />
                Telemetry Spans ({telemetrySpans.length})
              </div>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Node Executions Tab */}
          {activeTab === 'nodes' && (
            <div className="space-y-4">
              {nodeExecutions.length === 0 ? (
                <p className="text-center text-gray-600 py-8">No node executions recorded</p>
              ) : (
                nodeExecutions.map((node) => (
                  <div
                    key={node.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(node.status)}
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{node.node_name}</h3>
                          <p className="text-sm text-gray-600">{node.node_type}</p>
                        </div>
                      </div>
                      {getStatusBadge(node.status)}
                    </div>

                    {/* Node Timings */}
                    <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Prep Phase</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {formatDuration(node.prep_duration_ms)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Exec Phase</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {formatDuration(node.exec_duration_ms)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Post Phase</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {formatDuration(node.post_duration_ms)}
                        </p>
                      </div>
                    </div>

                    {/* Total Duration */}
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Total Duration:</span>
                        <span className="text-sm font-bold text-gray-900">
                          {formatDuration(
                            (node.prep_duration_ms || 0) + 
                            (node.exec_duration_ms || 0) + 
                            (node.post_duration_ms || 0)
                          )}
                        </span>
                      </div>
                    </div>

                    {/* Error Message */}
                    {node.error_message && (
                      <div className="mt-4 bg-red-50 border border-red-200 rounded p-3">
                        <p className="text-xs font-semibold text-red-900 mb-1">Error:</p>
                        <p className="text-xs text-red-800 font-mono">{node.error_message}</p>
                      </div>
                    )}

                    {/* Retry Info */}
                    {node.retry_count > 0 && (
                      <div className="mt-2">
                        <span className="text-xs text-orange-600">
                          Retried {node.retry_count} time(s)
                        </span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Telemetry Events Tab */}
          {activeTab === 'events' && (
            <div>
              {/* Filters */}
              <div className="mb-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 mb-3">
                  <Filter size={18} className="text-gray-600" />
                  <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Search */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Search
                    </label>
                    <div className="relative">
                      <Search size={16} className="absolute left-3 top-2.5 text-gray-400" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search events..."
                        className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  {/* Event Type Filter */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Event Type
                    </label>
                    <select
                      value={eventTypeFilter}
                      onChange={(e) => setEventTypeFilter(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {uniqueEventTypes.map(type => (
                        <option key={type} value={type}>
                          {type === 'all' ? 'All Types' : type}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Node Name Filter */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Node
                    </label>
                    <select
                      value={nodeNameFilter}
                      onChange={(e) => setNodeNameFilter(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {uniqueNodeNames.map(name => (
                        <option key={name} value={name}>
                          {name === 'all' ? 'All Nodes' : name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Clear Filters */}
                {(eventTypeFilter !== 'all' || nodeNameFilter !== 'all' || searchQuery) && (
                  <button
                    onClick={() => {
                      setEventTypeFilter('all');
                      setNodeNameFilter('all');
                      setSearchQuery('');
                    }}
                    className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Clear All Filters
                  </button>
                )}
              </div>

              {/* Events Table */}
              <div className="overflow-x-auto">
                {filteredEvents.length === 0 ? (
                  <p className="text-center text-gray-600 py-8">
                    {telemetryEvents.length === 0 
                      ? 'No telemetry events recorded' 
                      : 'No events match your filters'}
                  </p>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Timestamp</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Event Type</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Node</th>
                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Data</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {filteredEvents.map((event) => (
                        <tr key={event.id} className="hover:bg-gray-50">
                          <td className="py-3 px-4 text-xs text-gray-600">
                            {formatDate(event.timestamp)}
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {event.event_type}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-xs font-medium text-gray-900">
                            {getNodeNameFromEvent(event)}
                          </td>
                          <td className="py-3 px-4 text-xs text-gray-600">
                            <details className="cursor-pointer">
                              <summary className="text-blue-600 hover:text-blue-700">View Data</summary>
                              <pre className="mt-2 bg-gray-100 p-2 rounded text-xs overflow-auto max-h-96">
                                {JSON.stringify(event.data, null, 2)}
                              </pre>
                            </details>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* Telemetry Spans Tab */}
          {activeTab === 'spans' && (
            <div className="overflow-x-auto">
              {telemetrySpans.length === 0 ? (
                <div className="text-center py-12">
                  <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">No telemetry spans recorded</p>
                  <p className="text-sm text-gray-500">
                    Spans are used for distributed tracing and may not be enabled for this execution.
                  </p>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Name</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Status</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Duration</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Start Time</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700">Attributes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {telemetrySpans.map((span) => (
                      <tr key={span.id} className="hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium text-gray-900">
                          {span.name}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            span.status === 'OK' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {span.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {formatDuration(span.duration_ms)}
                        </td>
                        <td className="py-3 px-4 text-xs text-gray-600">
                          {formatDate(span.start_time)}
                        </td>
                        <td className="py-3 px-4 text-xs text-gray-600">
                          <details className="cursor-pointer">
                            <summary className="text-blue-600 hover:text-blue-700">View Attributes</summary>
                            <pre className="mt-2 bg-gray-100 p-2 rounded text-xs overflow-auto">
                              {JSON.stringify(span.attributes, null, 2)}
                            </pre>
                          </details>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
