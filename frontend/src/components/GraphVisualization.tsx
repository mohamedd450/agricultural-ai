import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Graph from 'graphology';

interface GraphVisualizationProps {
  graph: Graph | null;
}

const NODE_COLORS: Record<string, string> = {
  Disease: '#e63946',
  Symptom: '#f4a261',
  Crop: '#2a9d8f',
  Treatment: '#457b9d',
};

const LEGEND_ITEMS = [
  { type: 'Disease', color: '#e63946' },
  { type: 'Symptom', color: '#f4a261' },
  { type: 'Crop', color: '#2a9d8f' },
  { type: 'Treatment', color: '#457b9d' },
];

const GraphVisualization: React.FC<GraphVisualizationProps> = ({ graph }) => {
  const { t } = useTranslation();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const transformRef = useRef({ offsetX: 0, offsetY: 0, scale: 1 });
  const dragRef = useRef<{ dragging: boolean; lastX: number; lastY: number }>({
    dragging: false,
    lastX: 0,
    lastY: 0,
  });
  const hoveredNodeRef = useRef<string | null>(null);

  useEffect(() => {
    if (!graph || !canvasRef.current || !containerRef.current) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    };
    resize();

    // Layout: assign positions in a force-directed-like circle layout
    const nodes = graph.nodes();
    const nodeCount = nodes.length;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = Math.min(cx, cy) * 0.6;

    const positions: Record<string, { x: number; y: number }> = {};
    nodes.forEach((nodeId, i) => {
      const angle = (2 * Math.PI * i) / nodeCount;
      positions[nodeId] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });

    const draw = () => {
      const { offsetX, offsetY, scale } = transformRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(offsetX, offsetY);
      ctx.scale(scale, scale);

      // Draw edges
      graph.forEachEdge((edge, attrs, source, target) => {
        const from = positions[source];
        const to = positions[target];
        if (!from || !to) return;
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = '#ced4da';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Edge label
        if (attrs.label) {
          const mx = (from.x + to.x) / 2;
          const my = (from.y + to.y) / 2;
          ctx.fillStyle = '#868e96';
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(String(attrs.label), mx, my - 4);
        }
      });

      // Draw nodes
      graph.forEachNode((nodeId, attrs) => {
        const pos = positions[nodeId];
        if (!pos) return;
        const isHovered = hoveredNodeRef.current === nodeId;
        const r = isHovered ? 18 : 14;

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI);
        ctx.fillStyle = String(attrs.color || '#999');
        ctx.fill();
        if (isHovered) {
          ctx.strokeStyle = '#1b4332';
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Label
        ctx.fillStyle = '#212529';
        ctx.font = `${isHovered ? 'bold ' : ''}12px sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText(String(attrs.label || nodeId), pos.x, pos.y + r + 14);
      });

      ctx.restore();
    };

    draw();

    // Mouse interactions
    const getNodeAt = (mx: number, my: number): string | null => {
      const { offsetX, offsetY, scale } = transformRef.current;
      for (const nodeId of nodes) {
        const pos = positions[nodeId];
        const sx = pos.x * scale + offsetX;
        const sy = pos.y * scale + offsetY;
        const dist = Math.sqrt((mx - sx) ** 2 + (my - sy) ** 2);
        if (dist < 18 * scale) return nodeId;
      }
      return null;
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      if (dragRef.current.dragging) {
        transformRef.current.offsetX += mx - dragRef.current.lastX;
        transformRef.current.offsetY += my - dragRef.current.lastY;
        dragRef.current.lastX = mx;
        dragRef.current.lastY = my;
        draw();
        return;
      }

      const node = getNodeAt(mx, my);
      if (node !== hoveredNodeRef.current) {
        hoveredNodeRef.current = node;
        canvas.style.cursor = node ? 'pointer' : 'grab';
        draw();
      }
    };

    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      dragRef.current = {
        dragging: true,
        lastX: e.clientX - rect.left,
        lastY: e.clientY - rect.top,
      };
      canvas.style.cursor = 'grabbing';
    };

    const handleMouseUp = () => {
      dragRef.current.dragging = false;
      canvas.style.cursor = hoveredNodeRef.current ? 'pointer' : 'grab';
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 0.9;
      transformRef.current.scale = Math.min(
        5,
        Math.max(0.2, transformRef.current.scale * factor),
      );
      draw();
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel, { passive: false });

    const resizeObserver = new ResizeObserver(() => {
      resize();
      draw();
    });
    resizeObserver.observe(container);

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('mouseleave', handleMouseUp);
      canvas.removeEventListener('wheel', handleWheel);
      resizeObserver.disconnect();
    };
  }, [graph]);

  if (!graph || graph.order === 0) {
    return (
      <div
        style={{
          padding: 40,
          textAlign: 'center',
          color: '#868e96',
          background: 'white',
          borderRadius: 12,
          border: '1px solid #e9ecef',
        }}
      >
        {t('graph.noData')}
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'white',
        borderRadius: 12,
        border: '1px solid #e9ecef',
        overflow: 'hidden',
      }}
    >
      <div
        ref={containerRef}
        style={{ position: 'relative', height: 400, width: '100%' }}
      >
        <canvas
          ref={canvasRef}
          style={{ width: '100%', height: '100%', cursor: 'grab' }}
        />
      </div>

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          gap: 16,
          padding: '12px 16px',
          borderTop: '1px solid #e9ecef',
          background: '#fafafa',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 600, color: '#495057' }}>
          {t('graph.legend')}:
        </span>
        {LEGEND_ITEMS.map(({ type, color }) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: color,
              }}
            />
            <span style={{ fontSize: 12, color: '#495057' }}>
              {t(`graph.${type.toLowerCase()}`)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GraphVisualization;
