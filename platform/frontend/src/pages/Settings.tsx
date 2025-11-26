import { useEffect, useState } from 'react'
import { Key, Copy, Trash2, Plus } from 'lucide-react'
import { supabase } from '../lib/supabase'

interface ApiKey {
  id: string
  name: string
  key_prefix: string
  created_at: string
  last_used_at: string | null
}

export default function Settings() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [newKeyName, setNewKeyName] = useState('')
  const [generatedKey, setGeneratedKey] = useState<string | null>(null)
  const [showNewKeyForm, setShowNewKeyForm] = useState(false)

  useEffect(() => {
    loadApiKeys()
  }, [])

  const loadApiKeys = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { data, error } = await supabase
        .from('api_keys')
        .select('id, name, key_prefix, created_at, last_used_at')
        .order('created_at', { ascending: false })

      if (error) throw error
      setApiKeys(data || [])
    } catch (error) {
      console.error('Failed to load API keys:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateApiKey = async () => {
    if (!newKeyName.trim()) return

    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { data: orgData, error: orgError } = await supabase
        .from('user_organizations')
        .select('organization_id')
        .eq('user_id', user.id)
        .single()

      if (orgError || !orgData) {
        alert('No organization found. Please contact support.')
        return
      }

      const keyValue = `agora_${generateRandomString(32)}`
      const keyPrefix = keyValue.substring(0, 12)

      const keyHash = await hashString(keyValue)

      const { error } = await supabase
        .from('api_keys')
        .insert({
          organization_id: orgData.organization_id,
          name: newKeyName,
          key_hash: keyHash,
          key_prefix: keyPrefix
        })

      if (error) throw error

      setGeneratedKey(keyValue)
      setNewKeyName('')
      setShowNewKeyForm(false)
      await loadApiKeys()
    } catch (error) {
      console.error('Failed to generate API key:', error)
      alert('Failed to generate API key')
    }
  }

  const deleteApiKey = async (id: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return
    }

    try {
      const { error } = await supabase
        .from('api_keys')
        .delete()
        .eq('id', id)

      if (error) throw error
      await loadApiKeys()
    } catch (error) {
      console.error('Failed to delete API key:', error)
      alert('Failed to delete API key')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your API keys and preferences</p>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Key className="text-gray-600" size={24} />
              <div>
                <h2 className="text-xl font-semibold text-gray-900">API Keys</h2>
                <p className="text-sm text-gray-600">Use API keys to authenticate your Agora workflows</p>
              </div>
            </div>
            {!showNewKeyForm && (
              <button
                onClick={() => setShowNewKeyForm(true)}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
              >
                <Plus size={16} />
                New API Key
              </button>
            )}
          </div>
        </div>

        {generatedKey && (
          <div className="p-6 bg-green-50 border-b border-green-200">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <p className="text-sm font-semibold text-green-900 mb-2">
                  API Key Generated Successfully!
                </p>
                <p className="text-sm text-green-800 mb-3">
                  Make sure to copy your API key now. You won't be able to see it again!
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-white px-4 py-3 rounded border border-green-300 text-sm font-mono break-all">
                    {generatedKey}
                  </code>
                  <button
                    onClick={() => copyToClipboard(generatedKey)}
                    className="flex items-center gap-2 bg-green-600 text-white px-4 py-3 rounded hover:bg-green-700 transition"
                  >
                    <Copy size={16} />
                    Copy
                  </button>
                </div>
              </div>
              <button
                onClick={() => setGeneratedKey(null)}
                className="text-green-600 hover:text-green-700"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {showNewKeyForm && (
          <div className="p-6 bg-blue-50 border-b border-blue-200">
            <h3 className="font-semibold text-gray-900 mb-3">Create New API Key</h3>
            <div className="flex gap-3">
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Enter key name (e.g., 'Production Bot')"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={generateApiKey}
                disabled={!newKeyName.trim()}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
              >
                Generate
              </button>
              <button
                onClick={() => {
                  setShowNewKeyForm(false)
                  setNewKeyName('')
                }}
                className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300 transition"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : apiKeys.length === 0 ? (
          <div className="p-8 text-center">
            <Key className="mx-auto text-gray-400 mb-3" size={48} />
            <p className="text-gray-500 mb-4">No API keys yet</p>
            <p className="text-sm text-gray-400 mb-6">
              Create an API key to start sending telemetry data from your workflows
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {apiKeys.map((key) => (
              <div key={key.id} className="p-6 hover:bg-gray-50 transition">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{key.name}</h3>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                        {key.key_prefix}...
                      </code>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-600">
                      <span>Created {new Date(key.created_at).toLocaleDateString()}</span>
                      {key.last_used_at && (
                        <span>Last used {new Date(key.last_used_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => deleteApiKey(key.id)}
                    className="flex items-center gap-2 text-red-600 hover:text-red-700 px-3 py-2 rounded hover:bg-red-50 transition"
                  >
                    <Trash2 size={16} />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">Using Your API Key</h3>
        <p className="text-sm text-blue-800 mb-4">
          Add this code to your Python workflow to send telemetry to Agora Cloud:
        </p>
        <pre className="bg-white border border-blue-200 rounded p-4 text-sm overflow-x-auto">
          <code>{`import os
os.environ["AGORA_API_KEY"] = "agora_xxxxx"  # Your key

from agora.agora_tracer import init_traceloop

init_traceloop(
    app_name="my_workflow",
    api_key=os.environ["AGORA_API_KEY"]
)`}</code>
        </pre>
      </div>
    </div>
  )
}

function generateRandomString(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

async function hashString(str: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(str)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}
