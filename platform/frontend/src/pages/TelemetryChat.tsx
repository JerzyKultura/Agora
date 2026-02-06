import { useState } from 'react'
import { Send, Code, Table } from 'lucide-react'

interface Message {
    role: 'user' | 'assistant'
    content: string
    sql?: string
    data?: any[]
}

export default function TelemetryChat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: 'Ask me anything about your telemetry! Try: "How long did ChatTurn take?" or "Show me failed executions for premium users"'
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)

    const askQuestion = async () => {
        if (!input.trim()) return

        const userMessage: Message = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            // Call Python script (in production, this would be an API endpoint)
            const response = await fetch('/api/telemetry-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: input })
            })

            const data = await response.json()

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.answer,
                sql: data.sql,
                data: data.results
            }])
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Error: ${error instanceof Error ? error.message : 'Failed to query telemetry'}`
            }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
                <h1 className="text-2xl font-bold text-gray-900">💬 Ask About Your Telemetry</h1>
                <p className="text-sm text-gray-600 mt-1">Natural language queries powered by AI</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-3xl ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200'} rounded-lg p-4 shadow-sm`}>
                            {/* Message content */}
                            <div className={`text-sm ${msg.role === 'user' ? 'text-white' : 'text-gray-900'}`}>
                                {msg.content}
                            </div>

                            {/* SQL query (if present) */}
                            {msg.sql && (
                                <details className="mt-3">
                                    <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-900 flex items-center gap-1">
                                        <Code className="w-3 h-3" />
                                        View SQL
                                    </summary>
                                    <pre className="mt-2 p-3 bg-gray-900 text-gray-100 rounded text-xs overflow-x-auto">
                                        {msg.sql}
                                    </pre>
                                </details>
                            )}

                            {/* Data table (if present) */}
                            {msg.data && msg.data.length > 0 && (
                                <details className="mt-3">
                                    <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-900 flex items-center gap-1">
                                        <Table className="w-3 h-3" />
                                        View Data ({msg.data.length} rows)
                                    </summary>
                                    <div className="mt-2 overflow-x-auto">
                                        <table className="min-w-full text-xs">
                                            <thead className="bg-gray-100">
                                                <tr>
                                                    {Object.keys(msg.data[0]).map(key => (
                                                        <th key={key} className="px-3 py-2 text-left font-medium text-gray-700">
                                                            {key}
                                                        </th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-200">
                                                {msg.data.slice(0, 10).map((row, rowIdx) => (
                                                    <tr key={rowIdx}>
                                                        {Object.values(row).map((val: any, colIdx) => (
                                                            <td key={colIdx} className="px-3 py-2 text-gray-900">
                                                                {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        {msg.data.length > 10 && (
                                            <div className="text-xs text-gray-500 mt-2 text-center">
                                                Showing 10 of {msg.data.length} rows
                                            </div>
                                        )}
                                    </div>
                                </details>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                Thinking...
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="bg-white border-t border-gray-200 p-4">
                <div className="max-w-4xl mx-auto">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && !loading && askQuestion()}
                            placeholder="Ask about your telemetry... (e.g., 'How long did ChatTurn take?')"
                            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            disabled={loading}
                        />
                        <button
                            onClick={askQuestion}
                            disabled={loading || !input.trim()}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            <Send className="w-4 h-4" />
                            Ask
                        </button>
                    </div>

                    {/* Suggested questions */}
                    <div className="mt-3 flex flex-wrap gap-2">
                        <span className="text-xs text-gray-500">Try:</span>
                        {[
                            "How long did ChatTurn take?",
                            "Show me failed executions",
                            "What's my total cost this week?",
                            "Which workflows are slowest?"
                        ].map(q => (
                            <button
                                key={q}
                                onClick={() => setInput(q)}
                                className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700"
                            >
                                {q}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
