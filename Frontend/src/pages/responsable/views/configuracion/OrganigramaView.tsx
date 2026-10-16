import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modulo0Service, NodoOrganigrama } from '@/services/modulo0.service';
import { Button, getLogoDataUrl } from '@/components/ui';
import { FormField, Input, LoadingSpinner, ErrorDisplay } from '@/components/ui/forms';
import { useBranding } from '@/store/branding.context';
import { hexToHsl, hslToRgb, rgbToHex } from '@/utils/color.utils';
import { hierarchy, tree } from 'd3-hierarchy';
import {
  GitBranch, Plus, Trash2, Edit2, ZoomIn, ZoomOut, RotateCcw,
  Printer, ChevronDown, ChevronRight, ChevronUp, ChevronLeft,
  X, AlertTriangle, ShieldCheck, Loader2,
  Maximize2, Palette, Columns, Rows, Minimize2
} from 'lucide-react';

// --- Types & Interfaces ---

type Orientation = 'vertical' | 'horizontal';
type ColorMode = 'area' | 'nivel' | 'monocromo';

interface Point {
  x: number;
  y: number;
}

interface NodeWithPos extends NodoOrganigrama {
  _x: number;
  _y: number;
  _isHanging?: boolean;
  _collapsed?: boolean;
  children?: NodeWithPos[];
}

interface TreeNode {
  data: NodeWithPos;
  x: number;
  y: number;
  parent: TreeNode | null;
  children?: TreeNode[];
  _isHangingLeaf?: boolean;
}

// --- Utils ---

const generateAreaColors = (areas: string[], branding: any) => {
  const baseHsl = hexToHsl(branding?.primario || '#002D62');
  const colors: Record<string, string> = {};
  
  areas.forEach((area, i) => {
    const hue = (baseHsl.h + (i * 360 / Math.max(areas.length, 1))) % 360;
    const rgb = hslToRgb(hue, 60, 50);
    colors[area] = rgbToHex(rgb.r, rgb.g, rgb.b);
  });
  return colors;
};

const getLevelColor = (level: number, branding: any) => {
  if (level === 1) return branding?.primario || '#002D62';
  if (level === 2) return branding?.secundario || '#0284C7';
  if (level === 3) return branding?.acento || '#F5A800';
  
  const baseHsl = hexToHsl(branding?.primario || '#002D62');
  const rgb = hslToRgb(
    baseHsl.h,
    Math.max(10, baseHsl.s - (level * 10)),
    Math.min(85, baseHsl.l + (level * 10))
  );
  return rgbToHex(rgb.r, rgb.g, rgb.b);
};

const getMonochromeColor = () => '#94a3b8'; // slate-400

const generatePath = (source: Point, target: Point, orientation: Orientation, isHangingTarget: boolean = false) => {
  const radius = 8;
  if (orientation === 'vertical') {
    if (isHangingTarget) {
      const midY = source.y + 30;
      return `M ${source.x} ${source.y}
              L ${source.x} ${midY - radius}
              Q ${source.x} ${midY} ${source.x > target.x ? source.x - radius : source.x + radius} ${midY}
              L ${target.x < source.x ? target.x + radius : target.x - radius} ${midY}
              Q ${target.x} ${midY} ${target.x} ${midY + radius}
              L ${target.x} ${target.y}`;
    }

    const midY = source.y + (target.y - source.y) / 2;
    return `M ${source.x} ${source.y}
            L ${source.x} ${midY - radius}
            Q ${source.x} ${midY} ${source.x < target.x ? source.x + radius : source.x - radius} ${midY}
            L ${target.x < source.x ? target.x + radius : target.x - radius} ${midY}
            Q ${target.x} ${midY} ${target.x} ${midY + radius}
            L ${target.x} ${target.y}`;
  } else {
    if (isHangingTarget) {
      const midX = source.x + 30;
      return `M ${source.x} ${source.y}
              L ${midX - radius} ${source.y}
              Q ${midX} ${source.y} ${midX} ${source.y > target.y ? source.y - radius : source.y + radius}
              L ${midX} ${target.y < source.y ? target.y + radius : target.y - radius}
              Q ${midX} ${target.y} ${midX + radius} ${target.y}
              L ${target.x} ${target.y}`;
    }

    const midX = source.x + (target.x - source.x) / 2;
    return `M ${source.x} ${source.y}
            L ${midX - radius} ${source.y}
            Q ${midX} ${source.y} ${midX} ${source.y < target.y ? source.y - radius : source.y + radius}
            L ${midX} ${target.y < source.y ? target.y + radius : target.y - radius}
            Q ${midX} ${target.y} ${midX + radius} ${target.y}
            L ${target.x} ${target.y}`;
  }
};

// --- Main Component ---

export default function OrganigramaView() {
  const queryClient = useQueryClient();
  const { branding } = useBranding();
  
  // State
  const [orientation, setOrientation] = useState<Orientation>('vertical');
  const [colorMode, setColorMode] = useState<ColorMode>('area');
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set());
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Node Dragging State
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const [nodeDragStart, setNodeDragStart] = useState<{ x: number, y: number } | null>(null);
  const [nodeOffset, setNodeOffset] = useState<{ x: number, y: number } | null>(null);
  const [tempNodePositions, setTempNodePositions] = useState<Record<string, Point>>({});
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<NodoOrganigrama>>({});

  // Confirm Auto Organize State
  const [showAutoConfirm, setShowAutoConfirm] = useState(false);
  const [mutationError, setMutationError] = useState<string>('');

  const containerRef = useRef<HTMLDivElement>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const errMsg = (err: unknown, fallback: string) =>
    (err as any)?.friendlyMessage || (err as any)?.message || fallback;

  // Queries
  const { data: nodes = [], isLoading, isError } = useQuery({
    queryKey: ['modulo0', 'organigrama'],
    queryFn: modulo0Service.getOrganigrama
  });

  // Mutations
  const updateNodeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<NodoOrganigrama> }) => modulo0Service.updateNodo(id, data),
    onSuccess: () => {
      setMutationError('');
      setIsModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['modulo0'] });
    },
    onError: (err) => setMutationError(errMsg(err, 'No se pudo guardar el cargo.'))
  });

  const createNodeMutation = useMutation({
    mutationFn: modulo0Service.createNodo,
    onSuccess: () => {
      setMutationError('');
      queryClient.invalidateQueries({ queryKey: ['modulo0'] });
      setIsModalOpen(false);
    },
    onError: (err) => setMutationError(errMsg(err, 'No se pudo crear el cargo.'))
  });

  const deleteNodeMutation = useMutation({
    mutationFn: modulo0Service.deleteNodo,
    onSuccess: () => {
      setMutationError('');
      queryClient.invalidateQueries({ queryKey: ['modulo0'] });
    },
    onError: (err) => setMutationError(errMsg(err, 'No se pudo eliminar el cargo.'))
  });

  const autoOrganizeMutation = useMutation({
    mutationFn: modulo0Service.autoOrganizarOrganigrama,
    onSuccess: () => {
      setMutationError('');
      queryClient.invalidateQueries({ queryKey: ['modulo0'] });
      setShowAutoConfirm(false);
      setTimeout(() => fitToScreen(), 120);
    },
    onError: (err) => setMutationError(errMsg(err, 'No se pudo auto-organizar el organigrama.'))
  });

  const importBaseOrgMutation = useMutation({
    mutationFn: async () => {
      const gerencia = await modulo0Service.createNodo({
        nombre_cargo: 'Gerencia General / Representante Legal',
        area: 'Dirección General',
        padre_id: null,
        orden: 0
      });
      const respSST = await modulo0Service.createNodo({
        nombre_cargo: 'Responsable del SG-SST',
        area: 'Seguridad y Salud en el Trabajo',
        padre_id: gerencia.id,
        orden: 0
      });
      await modulo0Service.createNodo({
        nombre_cargo: 'COPASST / Vigía de SST',
        area: 'Comités Paritarios',
        padre_id: gerencia.id,
        orden: 1
      });
      await modulo0Service.createNodo({
        nombre_cargo: 'Comité de Convivencia Laboral',
        area: 'Comités Especiales',
        padre_id: gerencia.id,
        orden: 2
      });
      const operaciones = await modulo0Service.createNodo({
        nombre_cargo: 'Dirección / Jefatura de Operaciones',
        area: 'Operaciones',
        padre_id: gerencia.id,
        orden: 3
      });
      await modulo0Service.createNodo({
        nombre_cargo: 'Brigada de Emergencias y Primeros Auxilios',
        area: 'Seguridad y Salud en el Trabajo',
        padre_id: respSST.id,
        orden: 0
      });
      await modulo0Service.createNodo({
        nombre_cargo: 'Supervisores de Campo y Operaciones',
        area: 'Operaciones',
        padre_id: operaciones.id,
        orden: 0
      });
    },
    onSuccess: () => {
      setMutationError('');
      queryClient.invalidateQueries({ queryKey: ['modulo0'] });
      setTimeout(() => fitToScreen(), 150);
    },
    onError: (err) => setMutationError(errMsg(err, 'No se pudo cargar la estructura base.'))
  });

  // Tree computation
  const { layoutNodes, areas } = useMemo(() => {
    if (!nodes.length) return { layoutNodes: [], areas: [] };

    const areasList = Array.from(new Set(nodes.map(n => n.area).filter(Boolean))) as string[];

    const nodeMap = new Map<string, NodeWithPos>();
    nodes.forEach(n => {
      nodeMap.set(n.id, { ...n, _x: 0, _y: 0 });
    });

    const roots: NodeWithPos[] = [];
    const sortedNodes = [...nodes].sort((a, b) => a.orden - b.orden);

    sortedNodes.forEach(n => {
      const node = nodeMap.get(n.id)!;
      if (node.padre_id && nodeMap.has(node.padre_id)) {
        const parent = nodeMap.get(node.padre_id)!;
        if (!parent.children) parent.children = [];
        parent.children.push(node);
      } else {
        roots.push(node);
      }
    });

    if (roots.length === 0) return { layoutNodes: [], areas: areasList };

    let d3Root;
    if (roots.length === 1) {
      d3Root = hierarchy(roots[0]);
    } else {
      d3Root = hierarchy({ id: 'dummy', nombre_cargo: 'Root', children: roots } as any);
    }

    // Collapse
    d3Root.each(d => {
      const n = d.data as NodeWithPos;
      if (collapsedNodes.has(n.id)) {
        if (d.children) {
          (d as any)._children = d.children;
          d.children = undefined;
        }
      }
    });

    // Hanging nodes detection
    d3Root.each(d => {
      if (d.children && d.children.length > 4) {
        const allLeaves = d.children.every(c => !c.children || c.children.length === 0);
        if (allLeaves) {
          (d.data as NodeWithPos)._isHanging = true;
          d.children.forEach(c => {
            (c as any)._isHangingLeaf = true;
          });
        }
      }
    });

    const nodeSize: [number, number] = orientation === 'vertical' ? [300, 180] : [320, 150];
    const treeLayout = tree<NodeWithPos>().nodeSize(nodeSize);
    
    treeLayout.separation((a, b) => {
      if ((a as any)._isHangingLeaf || (b as any)._isHangingLeaf) {
        return 0.5;
      }
      return a.parent === b.parent ? 1 : 1.2;
    });

    treeLayout(d3Root);

    const layoutNodesList: TreeNode[] = [];
    
    d3Root.each((d: any) => {
      if (d.data.id === 'dummy') return;

      const nData = d.data as NodeWithPos;
      const isHangingLeaf = !!d._isHangingLeaf;
      
      let finalX: number = orientation === 'vertical' ? (d.x ?? 0) : (d.y ?? 0);
      let finalY: number = orientation === 'vertical' ? (d.y ?? 0) : (d.x ?? 0);

      if (isHangingLeaf && d.parent) {
        const pX: number = orientation === 'vertical' ? (d.parent.x ?? 0) : (d.parent.y ?? 0);
        const pY: number = orientation === 'vertical' ? (d.parent.y ?? 0) : (d.parent.x ?? 0);
        const childIndex = d.parent.children ? d.parent.children.indexOf(d) : 0;
        
        if (orientation === 'vertical') {
           finalX = pX;
           finalY = pY + 140 + (childIndex * 110);
        } else {
           finalX = pX + 280 + (childIndex * 220);
           finalY = pY;
        }
      }

      // DB overrides
      if (nData.pos_x !== null && nData.pos_x !== undefined) finalX = nData.pos_x;
      if (nData.pos_y !== null && nData.pos_y !== undefined) finalY = nData.pos_y;

      // Dragging overrides
      if (tempNodePositions[nData.id]) {
        finalX = tempNodePositions[nData.id].x;
        finalY = tempNodePositions[nData.id].y;
      }

      const parentNode = d.parent && d.parent.data.id !== 'dummy' ? {
        data: d.parent.data as NodeWithPos,
        x: (orientation === 'vertical' ? d.parent.x : d.parent.y) ?? 0,
        y: (orientation === 'vertical' ? d.parent.y : d.parent.x) ?? 0,
        parent: null
      } : null;

      layoutNodesList.push({
        data: { ...nData, _x: finalX, _y: finalY },
        x: finalX,
        y: finalY,
        parent: parentNode,
        _isHangingLeaf: isHangingLeaf
      });
    });

    return { layoutNodes: layoutNodesList, areas: areasList };
  }, [nodes, collapsedNodes, orientation, tempNodePositions]);

  // Color logic
  const areaColors = useMemo(() => generateAreaColors(areas, branding), [areas, branding]);

  const getNodeColor = useCallback((node: NodeWithPos) => {
    switch (colorMode) {
      case 'area':
        return node.area && areaColors[node.area] ? areaColors[node.area] : getMonochromeColor();
      case 'nivel':
        return getLevelColor(node.nivel, branding);
      case 'monocromo':
      default:
        return getMonochromeColor();
    }
  }, [colorMode, areaColors, branding]);

  // Viewport interactions
  const handleWheel = (e: React.WheelEvent) => {
    if (e.deltaY === 0) return;
    const zoomSensitivity = 0.001;
    const delta = -e.deltaY * zoomSensitivity;
    let newZoom = zoom * (1 + delta);
    newZoom = Math.max(0.15, Math.min(newZoom, 2.5));
    
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      const newPanX = mouseX - (mouseX - pan.x) * (newZoom / zoom);
      const newPanY = mouseY - (mouseY - pan.y) * (newZoom / zoom);
      
      setZoom(newZoom);
      setPan({ x: newPanX, y: newPanY });
    }
  };

  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.interactive-node-element')) return;
    if ((e.target as HTMLElement).closest('.node-card')) return;
    
    setIsDraggingCanvas(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (isDraggingCanvas) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    } else if (draggingNode && nodeDragStart && nodeOffset) {
      const dx = (e.clientX - nodeDragStart.x) / zoom;
      const dy = (e.clientY - nodeDragStart.y) / zoom;
      
      const rawX = nodeOffset.x + dx;
      const rawY = nodeOffset.y + dy;
      
      const snappedX = Math.round(rawX / 10) * 10;
      const snappedY = Math.round(rawY / 10) * 10;

      setTempNodePositions(prev => ({
        ...prev,
        [draggingNode]: { x: snappedX, y: snappedY }
      }));
    }
  };

  const handleCanvasMouseUp = () => {
    setIsDraggingCanvas(false);
    
    if (draggingNode && tempNodePositions[draggingNode]) {
      const pos = tempNodePositions[draggingNode];
      const nodeId = draggingNode;
      
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = setTimeout(() => {
        updateNodeMutation.mutate({
          id: nodeId,
          data: { pos_x: pos.x, pos_y: pos.y }
        });
      }, 300);
      
      setDraggingNode(null);
      setNodeDragStart(null);
      setNodeOffset(null);
    }
  };

  const handleNodeMouseDown = (e: React.MouseEvent, nodeId: string, currentX: number, currentY: number) => {
    if ((e.target as HTMLElement).closest('.interactive-node-element')) return;
    e.stopPropagation();
    
    setDraggingNode(nodeId);
    setNodeDragStart({ x: e.clientX, y: e.clientY });
    setNodeOffset({ x: currentX, y: currentY });
  };

  const fitToScreen = useCallback(() => {
    if (!containerRef.current || layoutNodes.length === 0) return;

    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = containerRef.current.clientHeight;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    layoutNodes.forEach(n => {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + 260);
      maxY = Math.max(maxY, n.y + 110);
    });

    const treeWidth = maxX - minX;
    const treeHeight = maxY - minY;

    const padding = 80;
    const scaleX = (containerWidth - padding * 2) / (treeWidth || 1);
    const scaleY = (containerHeight - padding * 2) / (treeHeight || 1);
    const newZoom = Math.max(0.2, Math.min(1.1, Math.min(scaleX, scaleY)));

    const newPanX = (containerWidth - treeWidth * newZoom) / 2 - minX * newZoom;
    const newPanY = orientation === 'vertical'
      ? Math.max(40, (containerHeight - treeHeight * newZoom) / 2) - minY * newZoom
      : (containerHeight - treeHeight * newZoom) / 2 - minY * newZoom;

    setZoom(newZoom);
    setPan({ x: newPanX, y: newPanY });
  }, [layoutNodes, orientation]);

  useEffect(() => {
    if (layoutNodes.length > 0 && zoom === 1 && pan.x === 0 && pan.y === 0) {
      fitToScreen();
    }
  }, [layoutNodes.length, fitToScreen, zoom, pan]);

  // Handlers
  const handleToggleCollapse = (nodeId: string) => {
    setCollapsedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const handleCreateChild = (parentId: string, parentNivel: number) => {
    setModalMode('create');
    setSelectedNodeId(null);
    setFormData({
      padre_id: parentId,
      nivel: parentNivel + 1,
      orden: 1,
      activo: true
    });
    setIsModalOpen(true);
  };

  const handleEdit = (node: NodoOrganigrama) => {
    setModalMode('edit');
    setSelectedNodeId(node.id);
    setFormData(node);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    if (confirm('¿Está seguro de eliminar este cargo?')) {
      deleteNodeMutation.mutate(id);
    }
  };

  const handleSaveModal = (e: React.FormEvent) => {
    e.preventDefault();
    if (modalMode === 'create') {
      createNodeMutation.mutate(formData as any);
    } else if (selectedNodeId) {
      // El modal se cierra en onSuccess (no antes), para no ocultar errores
      updateNodeMutation.mutate({ id: selectedNodeId, data: formData });
    }
  };

  const handlePrint = async () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    
    const logoDataUrl = await getLogoDataUrl((branding as any)?.logo_url);
    const primaryColor = branding?.primario || '#002D62';

    const logoHtml = logoDataUrl ? `
      <div style="width: 48px; height: 48px; border-radius: 12px; background: white; padding: 4px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.15); flex-shrink: 0;">
        <img src="${logoDataUrl}" style="max-width: 100%; max-height: 100%; object-fit: contain;" />
      </div>
    ` : '';

    const nodesHtml = [...nodes].sort((a, b) => a.nivel - b.nivel).map(n => `
      <div style="margin-left: ${(n.nivel - 1) * 20}px; margin-bottom: 8px; padding: 10px 14px; background: white; border: 1px solid #e2e8f0; border-left: 4px solid ${primaryColor}; border-radius: 10px; page-break-inside: avoid;">
        <div style="font-size: 10px; font-weight: bold; color: #64748b; text-transform: uppercase;">${n.area || 'Sin Área'}</div>
        <div style="font-size: 13px; font-weight: bold; color: #0f172a; margin-top: 2px;">${n.nombre_cargo}</div>
        <div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">Nivel Jerárquico: ${n.nivel} • Orden: ${n.orden}</div>
      </div>
    `).join('');

    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Organigrama Funcional SG-SST — Impresión</title>
          <meta charset="utf-8" />
          <style>
            @page { size: portrait; margin: 10mm; }
            body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 16px; }
            .header { background: ${primaryColor}; color: white; padding: 18px 22px; border-radius: 16px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
            .footer { text-align: center; font-size: 10px; color: #64748b; margin-top: 24px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-weight: 600; }
          </style>
        </head>
        <body>
          <div class="header">
            <div style="display: flex; align-items: center; gap: 14px;">
              ${logoHtml}
              <div>
                <div style="font-size: 10px; font-weight: 800; text-transform: uppercase; opacity: 0.9; letter-spacing: 0.5px;">ORGANIGRAMA FUNCIONAL DEL SG-SST</div>
                <div style="font-size: 16px; font-weight: 900; margin-top: 2px;">Estructura Jerárquica de Cargos</div>
              </div>
            </div>
            <div style="text-align: right; font-size: 10px; opacity: 0.85;">
              <div>Fecha: ${new Date().toLocaleDateString('es-CO')}</div>
              <div style="font-weight: 700; margin-top: 2px;">Documento Oficial FOSST V.I.D.A.</div>
            </div>
          </div>
          <div style="max-width: 900px; margin: 0 auto;">
            ${nodesHtml}
          </div>
          <div class="footer">
            FOSST V.I.D.A. — Sistema Integrado de Gestión de Seguridad y Salud en el Trabajo (ISO 45001 / Dec. 1072 de 2015)
          </div>
          <script>
            window.onload = function() {
              setTimeout(function() { window.print(); window.close(); }, 400);
            }
          </script>
        </body>
      </html>
    `;
    printWindow.document.write(html);
    printWindow.document.close();
  };

  const getValidParents = (currentNodeId: string | null) => {
    if (!currentNodeId) return nodes;
    
    const getDescendants = (id: string, all: NodoOrganigrama[]): string[] => {
      const children = all.filter(n => n.padre_id === id).map(n => n.id);
      let desc = [...children];
      children.forEach(c => {
        desc = [...desc, ...getDescendants(c, all)];
      });
      return desc;
    };

    const descendants = getDescendants(currentNodeId, nodes);
    return nodes.filter(n => n.id !== currentNodeId && !descendants.includes(n.id));
  };

  if (isLoading) return <div className="p-8 flex justify-center"><LoadingSpinner text="Cargando organigrama..." /></div>;
  if (isError) return <div className="p-8"><ErrorDisplay message="Error al cargar el organigrama" /></div>;

  return (
    <div
      className={
        isFullscreen
          ? "fixed inset-0 z-50 bg-slate-50 flex flex-col w-screen h-screen overflow-hidden"
          : "w-full h-[750px] min-h-[650px] flex flex-col bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden shadow-xs relative"
      }
    >
      {mutationError && (
        <div className="px-5 py-2 bg-red-50 border-b border-red-200 text-red-700 text-xs font-medium flex items-center justify-between">
          <span>{mutationError}</span>
          <button type="button" onClick={() => setMutationError('')} className="text-red-500 hover:text-red-700 font-bold">Cerrar</button>
        </div>
      )}

      {/* Toolbar en 2 zonas con flex-wrap */}
      <div className="relative z-10 bg-white border-b border-slate-200 px-5 py-3.5 flex flex-wrap items-center justify-between gap-4 shadow-2xs">
        {/* Zona Izquierda: Ícono + Título + Subtítulo */}
        <div className="flex items-center gap-3 min-w-[240px]">
          <div className="p-2.5 bg-brand-50 rounded-xl text-brand-600 border border-brand-100/60 shadow-2xs">
            <GitBranch size={22} />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-800 leading-tight">Organigrama Funcional</h1>
            <p className="text-xs text-slate-500">Gestión de la estructura organizacional</p>
          </div>
        </div>
        
        {/* Zona Derecha: Contador + Selector de Color + Acciones + Botón Primario */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Contador de Cargos */}
          <div className="text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200/80 px-3 py-1.5 rounded-full">
            {nodes.length} {nodes.length === 1 ? 'cargo' : 'cargos'}
          </div>

          {/* Selector Colorear Por */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1 text-xs">
            <Palette size={14} className="text-slate-500 flex-shrink-0" />
            <span className="text-[11px] font-medium text-slate-500">Color:</span>
            <select 
              value={colorMode}
              onChange={(e) => setColorMode(e.target.value as ColorMode)}
              className="bg-transparent border-none text-xs font-semibold text-slate-700 focus:ring-0 py-0.5 pl-1 pr-6 cursor-pointer"
            >
              <option value="area">Por Área</option>
              <option value="nivel">Por Nivel</option>
              <option value="monocromo">Monocromo</option>
            </select>
          </div>

          {/* Grupo de Acciones Secundarias (Orientación, Auto-organizar, Imprimir) */}
          <div className="inline-flex rounded-xl border border-slate-200 bg-white p-0.5 shadow-2xs">
            <button 
              type="button"
              onClick={() => setOrientation(o => o === 'vertical' ? 'horizontal' : 'vertical')}
              className="p-1.5 text-slate-600 hover:text-brand-600 hover:bg-slate-50 rounded-lg transition-colors"
              title={`Orientación: ${orientation === 'vertical' ? 'Vertical (Árbol)' : 'Horizontal'}`}
            >
              {orientation === 'vertical' ? <Columns size={16} /> : <Rows size={16} />}
            </button>
            <div className="w-px h-4 bg-slate-200 my-auto" />
            <button 
              type="button"
              onClick={() => setShowAutoConfirm(true)}
              className="p-1.5 text-slate-600 hover:text-brand-600 hover:bg-slate-50 rounded-lg transition-colors"
              title="Auto-organizar layout (eliminar posiciones manuales)"
            >
              <RotateCcw size={16} />
            </button>
            <div className="w-px h-4 bg-slate-200 my-auto" />
            <button 
              type="button"
              onClick={handlePrint}
              className="p-1.5 text-slate-600 hover:text-brand-600 hover:bg-slate-50 rounded-lg transition-colors"
              title="Imprimir organigrama"
            >
              <Printer size={16} />
            </button>
          </div>

          {/* Botón Primario: Nuevo Cargo */}
          <Button
            variant="primary"
            onClick={() => {
              setModalMode('create');
              setFormData({ nivel: 1, orden: 1, activo: true });
              setIsModalOpen(true);
            }}
            className="text-xs py-2 h-9"
          >
            <Plus size={15} className="mr-1.5" />
            Nuevo cargo
          </Button>
        </div>
      </div>

      {/* Estado Vacío cuando nodes.length === 0 */}
      {nodes.length === 0 ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center flex flex-col items-center">
            <div className="w-16 h-16 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-4 border border-brand-100 shadow-2xs">
              <GitBranch size={32} />
            </div>
            <h3 className="text-base font-bold text-slate-800 mb-1.5">
              Aún no has definido la estructura organizacional
            </h3>
            <p className="text-xs text-slate-500 mb-6 leading-relaxed">
              Crea los cargos jerárquicos de tu empresa o carga la estructura base preconfigurada según los requisitos normativos del SG-SST (Dec. 1072 de 2015 / Res. 0312 de 2019).
            </p>
            <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
              <Button
                variant="primary"
                onClick={() => importBaseOrgMutation.mutate()}
                disabled={importBaseOrgMutation.isPending}
                className="text-xs py-2 h-9 w-full sm:w-auto"
              >
                {importBaseOrgMutation.isPending ? (
                  <Loader2 size={15} className="animate-spin mr-1.5" />
                ) : (
                  <ShieldCheck size={15} className="mr-1.5" />
                )}
                Cargar estructura base SG-SST
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setModalMode('create');
                  setFormData({ nivel: 1, orden: 1, activo: true });
                  setIsModalOpen(true);
                }}
                className="text-xs py-2 h-9 w-full sm:w-auto border-slate-200 text-slate-700"
              >
                <Plus size={15} className="mr-1.5" />
                Crear primer cargo
              </Button>
            </div>
          </div>
        </div>
      ) : (
        /* Canvas Area */
        <div 
          ref={containerRef}
          className="flex-1 relative overflow-hidden w-full h-full"
          style={{
            cursor: isDraggingCanvas ? 'grabbing' : (draggingNode ? 'grabbing' : 'grab'),
            backgroundImage: 'radial-gradient(#cbd5e1 1.2px, transparent 1.2px)',
            backgroundSize: '22px 22px',
            backgroundPosition: `${pan.x}px ${pan.y}px`
          }}
          onWheel={handleWheel}
          onMouseDown={handleCanvasMouseDown}
          onMouseMove={handleCanvasMouseMove}
          onMouseUp={handleCanvasMouseUp}
          onMouseLeave={handleCanvasMouseUp}
        >
          <div 
            className="absolute origin-top-left transition-transform duration-75 ease-out"
            style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
          >
            {/* Edges */}
            <svg className="absolute top-0 left-0 overflow-visible pointer-events-none">
              {layoutNodes.map(node => {
                if (!node.parent) return null;
                
                const parentPos = layoutNodes.find(n => n.data.id === node.parent?.data.id);
                if (!parentPos) return null;

                let source: Point, target: Point;
                
                if (orientation === 'vertical') {
                  source = { x: parentPos.x + 120, y: parentPos.y + 100 };
                  target = { x: node.x + 120, y: node.y };
                } else {
                  source = { x: parentPos.x + 240, y: parentPos.y + 45 };
                  target = { x: node.x, y: node.y + 45 };
                }

                return (
                  <path
                    key={`edge-${node.data.id}`}
                    d={generatePath(source, target, orientation, node._isHangingLeaf)}
                    fill="none"
                    stroke="#CBD5E1"
                    strokeWidth={1.5}
                    className="transition-all duration-300"
                  />
                );
              })}
            </svg>

            {/* Nodes */}
            {layoutNodes.map(node => {
              const hasChildren = nodes.some(n => n.padre_id === node.data.id);
              const isCollapsed = collapsedNodes.has(node.data.id);
              const color = getNodeColor(node.data);
              const isDragging = draggingNode === node.data.id;
              
              return (
                <div
                  key={node.data.id}
                  className={`node-card absolute bg-white rounded-[14px] transition-all duration-200 group
                    ${isDragging ? 'shadow-2xl z-50 opacity-95 scale-105' : 'shadow-[0_1px_3px_rgba(0,0,0,0.08),0_1px_2px_rgba(0,0,0,0.06)] hover:shadow-lg hover:-translate-y-0.5 z-10'}
                  `}
                  style={{
                    transform: `translate(${node.x}px, ${node.y}px)`,
                    minWidth: '200px',
                    maxWidth: '280px',
                    borderLeft: `4px solid ${color}`,
                    cursor: isDragging ? 'grabbing' : 'grab'
                  }}
                  onMouseDown={(e) => handleNodeMouseDown(e, node.data.id, node.x, node.y)}
                >
                  <div className="p-3.5 relative">
                    {/* Floating actions overlay */}
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 interactive-node-element bg-white/95 backdrop-blur-xs rounded-lg p-1 shadow-sm border border-slate-100">
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleCreateChild(node.data.id, node.data.nivel); }} 
                        className="p-1 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-md transition-colors" 
                        title="Agregar subordinado"
                      >
                        <Plus size={14} />
                      </button>
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleEdit(node.data); }} 
                        className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors" 
                        title="Editar"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleDelete(node.data.id); }} 
                        className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors" 
                        title="Eliminar"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>

                    {/* Node Content */}
                    <div className="flex flex-col gap-1.5">
                      <div 
                        className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full inline-block w-fit"
                        style={{ backgroundColor: `${color}18`, color: color }}
                      >
                        {node.data.area || 'Sin Área'}
                      </div>
                      <div className="font-bold text-xs text-slate-850 line-clamp-2 leading-snug">
                        {node.data.nombre_cargo}
                      </div>
                    </div>
                  </div>

                  {/* Collapse Toggle */}
                  {hasChildren && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleToggleCollapse(node.data.id); }}
                      className="interactive-node-element absolute bg-white border border-slate-200 rounded-full p-0.5 shadow-xs text-slate-400 hover:text-brand-600 hover:border-brand-300 transition-colors z-20 flex items-center justify-center"
                      style={{
                        ...(orientation === 'vertical' ? {
                          bottom: -11,
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 22,
                          height: 22
                        } : {
                          right: -11,
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: 22,
                          height: 22
                        })
                      }}
                    >
                      {isCollapsed ? 
                        (orientation === 'vertical' ? <ChevronDown size={13} /> : <ChevronRight size={13} />) : 
                        (orientation === 'vertical' ? <ChevronUp size={13} /> : <ChevronLeft size={13} />)
                      }
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Floating Controls en la esquina inferior derecha del lienzo */}
          <div className="absolute bottom-6 right-6 flex flex-col items-center gap-1 bg-white rounded-xl shadow-lg border border-slate-200 p-1 z-20">
            <button 
              type="button"
              onClick={() => setZoom(z => Math.min(2.5, +(z + 0.15).toFixed(2)))} 
              className="p-2 text-slate-600 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors" 
              title="Acercar (+)"
            >
              <ZoomIn size={18} />
            </button>
            <div className="text-[11px] text-center font-bold text-slate-500 py-1 w-10 border-y border-slate-100 select-none">
              {Math.round(zoom * 100)}%
            </div>
            <button 
              type="button"
              onClick={() => setZoom(z => Math.max(0.15, +(z - 0.15).toFixed(2)))} 
              className="p-2 text-slate-600 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors" 
              title="Alejar (-)"
            >
              <ZoomOut size={18} />
            </button>
            <div className="h-px w-6 bg-slate-200 my-0.5" />
            <button 
              type="button"
              onClick={fitToScreen} 
              className="p-2 text-slate-600 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors" 
              title="Ajustar a pantalla"
            >
              <Maximize2 size={18} />
            </button>
            <button 
              type="button"
              onClick={() => setIsFullscreen(f => !f)} 
              className="p-2 text-slate-600 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors" 
              title={isFullscreen ? "Salir de pantalla completa" : "Pantalla completa"}
            >
              {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} className="rotate-90" />}
            </button>
          </div>

          {/* Minimapa en la esquina inferior izquierda del lienzo */}
          {layoutNodes.length > 0 && (
            <div className="absolute bottom-6 left-6 w-[200px] h-[140px] bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden z-20 opacity-90 hover:opacity-100 transition-opacity cursor-pointer">
              <div className="relative w-full h-full p-2">
                {(() => {
                  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                  layoutNodes.forEach(n => {
                    minX = Math.min(minX, n.x);
                    minY = Math.min(minY, n.y);
                    maxX = Math.max(maxX, n.x + 260);
                    maxY = Math.max(maxY, n.y + 110);
                  });

                  const scaleX = (184) / (maxX - minX || 1);
                  const scaleY = (124) / (maxY - minY || 1);
                  const scale = Math.min(scaleX, scaleY) * 0.9;
                  
                  const offsetX = 8 + (184 - (maxX - minX) * scale) / 2;
                  const offsetY = 8 + (124 - (maxY - minY) * scale) / 2;

                  return (
                    <>
                      {layoutNodes.map(n => (
                        <div 
                          key={`mini-${n.data.id}`}
                          className="absolute rounded-[1px]"
                          style={{
                            left: offsetX + (n.x - minX) * scale,
                            top: offsetY + (n.y - minY) * scale,
                            width: 200 * scale,
                            height: 70 * scale,
                            backgroundColor: getNodeColor(n.data)
                          }}
                        />
                      ))}
                      
                      {containerRef.current && (
                        <div 
                          className="absolute border-2 border-brand-500/60 bg-brand-500/10 pointer-events-none transition-all duration-75"
                          style={{
                            left: offsetX + (-pan.x / zoom - minX) * scale,
                            top: offsetY + (-pan.y / zoom - minY) * scale,
                            width: (containerRef.current.clientWidth / zoom) * scale,
                            height: (containerRef.current.clientHeight / zoom) * scale
                          }}
                        />
                      )}
                    </>
                  );
                })()}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Form Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h2 className="text-base font-bold text-slate-850">
                {modalMode === 'create' ? 'Nuevo Cargo' : 'Editar Cargo'}
              </h2>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              <form id="node-form" onSubmit={handleSaveModal} className="space-y-4">
                <FormField label="Nombre del Cargo" required>
                  <Input 
                    value={formData.nombre_cargo || ''}
                    onChange={e => setFormData({...formData, nombre_cargo: e.target.value})}
                    placeholder="Ej. Gerente Comercial"
                    required
                  />
                </FormField>

                <FormField label="Área / Departamento">
                  <Input 
                    value={formData.area || ''}
                    onChange={e => setFormData({...formData, area: e.target.value})}
                    placeholder="Ej. Ventas"
                  />
                </FormField>

                <FormField label="Reporta a (Cargo Superior)">
                  <select
                    className="w-full rounded-xl border border-slate-200 text-xs py-2 px-3 focus:border-brand-500 focus:ring-brand-500"
                    value={formData.padre_id || ''}
                    onChange={e => setFormData({...formData, padre_id: e.target.value || null})}
                  >
                    <option value="">-- Ninguno (Raíz) --</option>
                    {getValidParents(selectedNodeId).map(n => (
                      <option key={n.id} value={n.id}>{n.nombre_cargo} ({n.area || 'Sin área'})</option>
                    ))}
                  </select>
                </FormField>

                {modalMode === 'edit' && (
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="Nivel Jerárquico">
                      <Input 
                        value={formData.nivel || ''}
                        disabled
                        className="bg-slate-50 text-slate-500"
                      />
                    </FormField>
                    <FormField label="Orden (Posición)">
                      <Input 
                        type="number"
                        value={formData.orden || ''}
                        onChange={e => setFormData({...formData, orden: parseInt(e.target.value) || 0})}
                      />
                    </FormField>
                  </div>
                )}
                
                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="activo"
                    checked={formData.activo !== false}
                    onChange={e => setFormData({...formData, activo: e.target.checked})}
                    className="rounded text-brand-600 focus:ring-brand-500 border-slate-300"
                  />
                  <label htmlFor="activo" className="text-xs font-medium text-slate-700">Cargo Activo</label>
                </div>
              </form>
            </div>

            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setIsModalOpen(false)} className="text-xs py-2 h-9">
                Cancelar
              </Button>
              <Button 
                type="button" 
                variant="primary"
                onClick={() => {
                  const f = document.getElementById('node-form') as HTMLFormElement;
                  if (f) f.requestSubmit();
                }}
                disabled={createNodeMutation.isPending || updateNodeMutation.isPending}
                className="text-xs py-2 h-9"
              >
                {(createNodeMutation.isPending || updateNodeMutation.isPending) ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                ) : null}
                Guardar Cargo
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Auto Organize Confirm Modal */}
      {showAutoConfirm && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden flex flex-col">
            <div className="p-6 flex flex-col items-center text-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center">
                <AlertTriangle size={24} />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800 mb-1">¿Auto-organizar posiciones?</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Esta acción restablecerá todas las posiciones manuales y aplicará un diseño compacto de árbol. No se puede deshacer.
                </p>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setShowAutoConfirm(false)} className="text-xs py-2 h-9">
                Cancelar
              </Button>
              <Button 
                variant="primary" 
                className="bg-amber-500 hover:bg-amber-600 text-white border-transparent text-xs py-2 h-9"
                onClick={() => autoOrganizeMutation.mutate()} 
                disabled={autoOrganizeMutation.isPending}
              >
                {autoOrganizeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : null}
                Sí, organizar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}