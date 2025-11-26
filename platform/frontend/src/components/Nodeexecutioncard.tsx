import { useState } from 'react';
import { Clock, ChevronDown, ChevronRight, ArrowRight } from 'lucide-react';

interface TelemetrySpan {
  span_id: string;
  name: string;
  start_time: string;
  end_time: string;
  status: string;
  attributes: Record<string, any>;
}

interface NodeExecutionCardProps {
  node: {
    node_id: string;
    node_name: string;
    status: string;
    start_time: string;
    end_time: string;
    duration_ms: number;
    error_message?: string;
  };
  spans: TelemetrySpan[];
}

export function NodeExecutionCard({ node, spans }: NodeExecutionCardProps) {
  const [expandedPhase, setExpandedPhase] = useState<string | null>(null);

  // Group spans by phase
  const prepSpan = spans.find((s) => s.attributes?.['agora.phase'] === 'prep');
  const execSpan = spans.find((s) => s.attributes?.['agora.phase'] === 'exec');
  const postSpan = spans.find((s) => s.attributes?.['agora.phase'] === 'post');

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'success':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'prep':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'exec':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'post':
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="border border-gray-300 rounded-lg p-4 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h4 className="text-lg font-semibold text-gray-900">{node.node_name}</h4>
          <span className={`px-2 py-1 rounded text-xs font-semibold border ${getStatusColor(node.status)}`}>
            {node.status}
          </span>
        </div>
        <div className="text-sm text-gray-600">
          <Clock className="w-4 h-4 inline mr-1" />
          Total: {formatDuration(node.duration_ms)}
        </div>
      </div>

      {/* Phase Pills */}
      <div className="space-y-2">
        {/* Prep Phase */}
        <div>
          <button
            onClick={() => setExpandedPhase(expandedPhase === 'prep' ? null : 'prep')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border ${getPhaseColor('prep')} hover:opacity-80 transition-opacity`}
          >
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">📥 Prep</span>
              <span className="text-xs">
                {prepSpan ? formatDuration(prepSpan.attributes?.duration_ms || 0) : 'N/A'}
              </span>
            </div>
            {expandedPhase === 'prep' ? (
              <ChevronDown className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-600" />
            )}
          </button>
          
          {expandedPhase === 'prep' && prepSpan && (
            <div className="mt-2 ml-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="space-y-2">
                <div>
                  <span className="text-xs font-semibold text-gray-700">📥 Input Data:</span>
                  <pre className="mt-1 text-xs bg-white p-2 rounded border border-gray-300 overflow-auto max-h-40">
                    {JSON.stringify(prepSpan.attributes, null, 2)}
                  </pre>
                </div>
                <div className="text-xs text-gray-600">
                  <Clock className="w-3 h-3 inline mr-1" />
                  Preparation phase - loading context and validating inputs
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Exec Phase */}
        <div>
          <button
            onClick={() => setExpandedPhase(expandedPhase === 'exec' ? null : 'exec')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border ${getPhaseColor('exec')} hover:opacity-80 transition-opacity`}
          >
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">⚙️ Exec</span>
              <span className="text-xs">
                {execSpan ? formatDuration(execSpan.attributes?.duration_ms || 0) : 'N/A'}
              </span>
            </div>
            {expandedPhase === 'exec' ? (
              <ChevronDown className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-600" />
            )}
          </button>
          
          {expandedPhase === 'exec' && execSpan && (
            <div className="mt-2 ml-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="space-y-2">
                <div>
                  <span className="text-xs font-semibold text-gray-700">⚙️ Execution Details:</span>
                  <pre className="mt-1 text-xs bg-white p-2 rounded border border-gray-300 overflow-auto max-h-40">
                    {JSON.stringify(execSpan.attributes, null, 2)}
                  </pre>
                </div>
                {execSpan.attributes?.retry_count !== undefined && (
                  <div className="text-xs text-gray-600">
                    🔄 Retry count: {execSpan.attributes.retry_count}
                  </div>
                )}
                <div className="text-xs text-gray-600">
                  <Clock className="w-3 h-3 inline mr-1" />
                  Execution phase - main processing logic
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Post Phase */}
        <div>
          <button
            onClick={() => setExpandedPhase(expandedPhase === 'post' ? null : 'post')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg border ${getPhaseColor('post')} hover:opacity-80 transition-opacity`}
          >
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">📤 Post</span>
              <span className="text-xs">
                {postSpan ? formatDuration(postSpan.attributes?.duration_ms || 0) : 'N/A'}
              </span>
            </div>
            {expandedPhase === 'post' ? (
              <ChevronDown className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-600" />
            )}
          </button>
          
          {expandedPhase === 'post' && postSpan && (
            <div className="mt-2 ml-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="space-y-2">
                <div>
                  <span className="text-xs font-semibold text-gray-700">📤 Output & Routing:</span>
                  <pre className="mt-1 text-xs bg-white p-2 rounded border border-gray-300 overflow-auto max-h-40">
                    {JSON.stringify(postSpan.attributes, null, 2)}
                  </pre>
                </div>
                {postSpan.attributes?.next_action && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-600">Routes to:</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-semibold">
                      {postSpan.attributes.next_action}
                    </span>
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                )}
                <div className="text-xs text-gray-600">
                  <Clock className="w-3 h-3 inline mr-1" />
                  Post-processing - storing results and routing
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {node.error_message && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-red-900 mb-1">❌ Error:</p>
          <p className="text-xs text-red-800 font-mono">{node.error_message}</p>
        </div>
      )}
    </div>
  );
}
