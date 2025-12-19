import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

interface WorkflowGraphProps {
    nodes?: Array<{ id: string; label: string; type?: string }>;
    edges?: Array<{ source: string; target: string; label?: string }>;
    onNodeClick?: (nodeId: string) => void;
}

export default function WorkflowGraph({ nodes = [], edges = [], onNodeClick }: WorkflowGraphProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<cytoscape.Core | null>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Transform props to Cytoscape elements
        const elements = [
            ...nodes.map(n => ({
                data: {
                    id: n.id,
                    label: n.label,
                    type: n.type || 'default'
                }
            })),
            ...edges.map(e => ({
                data: {
                    source: e.source,
                    target: e.target,
                    label: e.label || ''
                }
            }))
        ];

        cyRef.current = cytoscape({
            container: containerRef.current,
            elements: elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'background-color': '#fff',
                        'border-width': 2,
                        'border-color': '#475569', // slate-600
                        'width': 140,
                        'height': 45,
                        'padding': '16px',
                        'shape': 'round-rectangle',
                        'font-size': '13px',
                        'font-weight': 600,
                        'font-family': 'Inter, system-ui, sans-serif',
                        'text-wrap': 'ellipsis',
                        'text-max-width': '120px',
                        'color': '#1e293b'
                    }
                },
                {
                    selector: 'node[type="start"]',
                    style: {
                        'border-color': '#059669', // emerald-600
                        'background-color': '#ecfdf5',
                        'border-width': 3
                    }
                },
                {
                    selector: 'node[type="end"]',
                    style: {
                        'border-color': '#dc2626', // red-600
                        'background-color': '#fef2f2',
                        'border-width': 3
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 3,
                        'line-color': '#94a3b8', // slate-400 (darker than before)
                        'target-arrow-color': '#94a3b8',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier', // switched to bezier for better visibility
                        'label': 'data(label)',
                        'font-size': '11px',
                        'text-background-color': '#fff',
                        'text-background-opacity': 1,
                        'text-background-padding': '4px',
                        'text-rotation': 'autorotate',
                        'color': '#64748b'
                    }
                },
                {
                    selector: 'node:selected',
                    style: {
                        'border-color': '#2563eb', // blue-600
                        'border-width': 4,
                        'background-color': '#eff6ff'
                    }
                }
            ],
            layout: {
                name: 'breadthfirst',
                directed: true,
                padding: 100,
                spacingFactor: 1.2,
                animate: true
            }
        });

        cyRef.current.on('tap', 'node', function (evt) {
            const node = evt.target;
            onNodeClick?.(node.id());
        });

        // Cleanup
        return () => {
            if (cyRef.current) {
                cyRef.current.destroy();
            }
        };
    }, [nodes, edges, onNodeClick]);

    return (
        <div
            ref={containerRef}
            className="w-full h-[600px] border border-gray-200 rounded-lg bg-gray-50"
        />
    );
}
