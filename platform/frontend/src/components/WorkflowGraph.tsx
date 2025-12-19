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
                        'border-color': '#64748b', // slate-500
                        'width': 120,
                        'height': 40,
                        'padding': '12px',
                        'shape': 'round-rectangle',
                        'font-size': '12px',
                        'font-family': 'Inter, sans-serif',
                        'text-wrap': 'ellipsis',
                        'text-max-width': '100px'
                    }
                },
                {
                    selector: 'node[type="start"]',
                    style: {
                        'border-color': '#10b981', // emerald-500
                        'background-color': '#f0fdf4'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#cbd5e1', // slate-300
                        'target-arrow-color': '#cbd5e1',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '12px',
                        'text-background-color': '#fff',
                        'text-background-opacity': 1,
                        'text-background-padding': '4px',
                        'text-rotation': 'autorotate'
                    }
                }
            ],
            layout: {
                name: 'breadthfirst',
                directed: true,
                spacingFactor: 1.5,
                padding: 50
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
