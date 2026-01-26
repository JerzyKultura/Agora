import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { Building2, Users, Copy, Check } from 'lucide-react'

interface Organization {
    id: string
    name: string
    created_at: string
    updated_at: string
}

interface UserOrganization {
    role: string
    organization: Organization
}

export default function Organizations() {
    const [userOrgs, setUserOrgs] = useState<UserOrganization[]>([])
    const [loading, setLoading] = useState(true)
    const [copiedId, setCopiedId] = useState<string | null>(null)

    useEffect(() => {
        loadOrganizations()
    }, [])

    const loadOrganizations = async () => {
        try {
            const { data: { user } } = await supabase.auth.getUser()
            if (!user) return

            const { data, error } = await supabase
                .from('user_organizations')
                .select(`
          role,
          organization:organizations(*)
        `)
                .eq('user_id', user.id)

            if (error) throw error

            setUserOrgs(data as any || [])
        } catch (error) {
            console.error('Failed to load organizations:', error)
        } finally {
            setLoading(false)
        }
    }

    const copyToClipboard = (text: string, id: string) => {
        navigator.clipboard.writeText(text)
        setCopiedId(id)
        setTimeout(() => setCopiedId(null), 2000)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-gray-500">Loading organizations...</div>
            </div>
        )
    }

    return (
        <div className="p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-3 mb-6">
                    <Building2 className="w-8 h-8 text-blue-600" />
                    <h1 className="text-3xl font-bold text-gray-900">Organizations</h1>
                </div>

                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                    {userOrgs.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                            <Building2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                            <p>No organizations found</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {userOrgs.map((userOrg) => {
                                const org = userOrg.organization
                                return (
                                    <div key={org.id} className="p-6">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h2 className="text-xl font-semibold text-gray-900">
                                                        {org.name}
                                                    </h2>
                                                    <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded">
                                                        {userOrg.role}
                                                    </span>
                                                </div>

                                                <div className="space-y-2 mt-4">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-sm text-gray-500 w-32">Organization ID:</span>
                                                        <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono text-gray-700">
                                                            {org.id}
                                                        </code>
                                                        <button
                                                            onClick={() => copyToClipboard(org.id, org.id)}
                                                            className="p-1 hover:bg-gray-100 rounded transition-colors"
                                                            title="Copy to clipboard"
                                                        >
                                                            {copiedId === org.id ? (
                                                                <Check className="w-4 h-4 text-green-600" />
                                                            ) : (
                                                                <Copy className="w-4 h-4 text-gray-400" />
                                                            )}
                                                        </button>
                                                    </div>

                                                    <div className="flex items-center gap-2">
                                                        <span className="text-sm text-gray-500 w-32">Created:</span>
                                                        <span className="text-sm text-gray-700">
                                                            {new Date(org.created_at).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                </div>

                                                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                                                    <div className="flex items-start gap-2">
                                                        <Users className="w-5 h-5 text-blue-600 mt-0.5" />
                                                        <div>
                                                            <h3 className="text-sm font-medium text-blue-900 mb-1">
                                                                Add to .env file
                                                            </h3>
                                                            <p className="text-sm text-blue-700 mb-2">
                                                                Use this organization ID in your Python scripts:
                                                            </p>
                                                            <code className="block text-sm bg-white px-3 py-2 rounded border border-blue-200 font-mono text-gray-800">
                                                                AGORA_ORG_ID="{org.id}"
                                                            </code>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>

                <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <h3 className="text-sm font-medium text-gray-900 mb-2">
                        💡 How Organizations Work
                    </h3>
                    <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Each user account automatically gets an organization when signing up</li>
                        <li>• All your projects, workflows, and telemetry belong to your organization</li>
                        <li>• You can only see data from organizations you're a member of</li>
                        <li>• Use the Organization ID in your .env file to link Python scripts to this organization</li>
                    </ul>
                </div>
            </div>
        </div>
    )
}
