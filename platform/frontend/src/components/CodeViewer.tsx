import Editor from '@monaco-editor/react';

interface CodeViewerProps {
    code: string;
    language?: string;
    readOnly?: boolean;
}

export default function CodeViewer({
    code,
    language = 'python',
    readOnly = true
}: CodeViewerProps) {
    return (
        <div className="h-full w-full border border-gray-200 rounded-lg overflow-hidden bg-[#1e1e1e]">
            <Editor
                height="100%"
                defaultLanguage={language}
                value={code}
                theme="vs-dark"
                options={{
                    readOnly,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    padding: { top: 16 }
                }}
            />
        </div>
    );
}
