import React, { useEffect, useState } from 'react';
import { Copy, Plus, Trash2, Key, AlertCircle } from 'lucide-react';
import api from '../lib/api';

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
}

interface NewKeyResponse {
  id: string;
  name: string;
  key: string;  // Full key - only shown once!
  key_prefix: string;
  warning: string;
}

export default function APIKeys() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<NewKeyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load API keys
  const loadKeys = async () => {
    try {
      setLoading(true);
      const data = await api.apiKeys.list();
      setKeys(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  // Create new API key
  const handleCreate = async () => {
    if (!newKeyName.trim()) {
      setError('Please enter a key name');
      return;
    }

    try {
      setCreating(true);
      setError(null);
      const newKey = await api.apiKeys.create({ name: newKeyName });
      setNewlyCreatedKey(newKey);
      setNewKeyName('');
      await loadKeys();
    } catch (err: any) {
      setError(err.message || 'Failed to create API key');
    } finally {
      setCreating(false);
    }
  };

  // Revoke API key
  const handleRevoke = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      return;
    }

    try {
      await api.apiKeys.revoke(keyId);
      await loadKeys();
    } catch (err: any) {
      setError(err.message || 'Failed to revoke API key');
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">API Keys</h1>
        <p className="text-gray-600">
          Generate API keys to authenticate your Agora workflows. Keep your keys secure and never share them publicly.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* New Key Created Modal */}
      {newlyCreatedKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <div className="flex items-center gap-3 mb-4">
              <Key className="w-6 h-6 text-green-600" />
              <h2 className="text-2xl font-bold text-gray-900">API Key Created!</h2>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p className="text-yellow-800 font-semibold mb-2">⚠️ Save this key now!</p>
              <p className="text-yellow-700 text-sm">
                This is the only time you'll see the full key. Store it securely - we can't recover it.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">API Key</label>
                <button
                  onClick={() => copyToClipboard(newlyCreatedKey.key)}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
                >
                  <Copy className="w-4 h-4" />
                  Copy
                </button>
              </div>
              <code className="block bg-white border border-gray-300 rounded p-3 font-mono text-sm break-all">
                {newlyCreatedKey.key}
              </code>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-blue-900 mb-2">How to use this key:</h3>
              <pre className="bg-white border border-blue-300 rounded p-3 text-sm overflow-x-auto">
{`from agora.cloud_client import CloudAuditLogger

logger = CloudAuditLogger(
    api_key="${newlyCreatedKey.key}",
    workflow_name="MyWorkflow"
)

# Use with your Agora nodes/flows
# Telemetry is automatically sent!`}
              </pre>
            </div>

            <button
              onClick={() => setNewlyCreatedKey(null)}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition"
            >
              I've Saved My Key
            </button>
          </div>
        </div>
      )}

      {/* Create New Key Button */}
      <div className="mb-6">
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          <Plus className="w-5 h-5" />
          Generate New API Key
        </button>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create API Key</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Key Name
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production Workflows"
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewKeyName('');
                  setError(null);
                }}
                className="flex-1 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={creating}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
              >
                {creating ? 'Creating...' : 'Create Key'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600"></div>
          <p className="text-gray-600 mt-4">Loading API keys...</p>
        </div>
      ) : keys.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Key className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No API Keys Yet</h3>
          <p className="text-gray-600 mb-4">
            Create your first API key to start sending telemetry from your Agora workflows.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            <Plus className="w-5 h-5" />
            Generate API Key
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Name</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Key</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Created</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Last Used</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {keys.map((key) => (
                <tr key={key.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <span className="font-medium text-gray-900">{key.name}</span>
                  </td>
                  <td className="py-3 px-4">
                    <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                      {key.key_prefix}...
                    </code>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="py-3 px-4">
                    {key.revoked_at ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Revoked
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Active
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    {!key.revoked_at && (
                      <button
                        onClick={() => handleRevoke(key.id)}
                        className="text-red-600 hover:text-red-700 p-2 rounded hover:bg-red-50 transition"
                        title="Revoke key"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}