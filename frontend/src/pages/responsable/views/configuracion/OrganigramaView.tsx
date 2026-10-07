import { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, NodoOrganigrama } from '@/services/modulo0.service'
import { Card, Button } from '@/components/ui'
import { FormField, Input, LoadingSpinner, ErrorDisplay } from '@/components/ui/forms'
import {
  GitBranch, Plus, Trash2, Edit2, ZoomIn, ZoomOut, RotateCcw,
  Printer, ChevronDown, ChevronRight, X, AlertTriangle, Users, Briefcase,
  ShieldCheck, Loader2
} from 'lucide-react'

interface TreeNode extends NodoOrganigrama {
  children: TreeNode[]
}

const customStyles = `
  .organigrama-canvas {
    background-color: #f8fafc;
    background-image: radial-gradient(#e2e8f0 1.5px, transparent 1.5px);
    background-size: 24px 24px;
  }
  .node-card {
    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
  }
  .node-card:hover {
    transform: translateY(-4px);
  }
  @media print {
    body {
      background: white !important;
      color: black !important;
    }
    #organigrama-root-view {
      border: none !important;
      background: white !important;
    }
    .no-print {
      display: none !important;
    }
    .organigrama-viewport-container {
      position: absolute !important;
      left: 0 !important;
      top: 0 !important;
      width: 100% !important;
      height: 100% !important;
      overflow: visible !important;
      background: white !important;
    }
    .organigrama-canvas {
      transform: none !important;
      background: none !important;
      position: relative !important;
      width: 100% !important;
      height: 100% !important;
    }
    .node-card {
      background: white !important;
      color: black !important;
      border: 1px solid #cbd5e1 !important;
      box-shadow: none !important;
      transform: none !important;
    }
    .node-card * {
      color: black !important;
    }
    .svg-connector-path {
      stroke: #94a3b8 !important;
      stroke-width: 2px !important;
    }
  }
`

export default function OrganigramaView() {
  const queryClient = useQueryClient()
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Modal states
  const [modalOpen, setModalOpen] = useState(false)
  const [editingNodo, setEditingNodo] = useState<NodoOrganigrama | null>(null)
  const [nombreCargo, setNombreCargo] = useState('')
  const [area, setArea] = useState('')
  const [padreId, setPadreId] = useState<string>('')
  const [orden, setOrden] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')

  // Viewport states
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [collapsedNodes, setCollapsedNodes] = useState<Record<string, boolean>>({})
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({})

  // Interactive states
  const [inlineEditingId, setInlineEditingId] = useState<string | null>(null)
  const [inlineEditValue, setInlineEditValue] = useState('')

  // Refs for tracking drag/pan states globally
  const isDraggingNodeRef = useRef(false)
  const draggedNodeIdRef = useRef<string | null>(null)
  const dragStartPosRef = useRef({ x: 0, y: 0 })
  const initialNodePosRef = useRef({ x: 0, y: 0 })

  const isPanningRef = useRef(false)
  const panStartPosRef = useRef({ x: 0, y: 0 })
  const initialPanRef = useRef({ x: 0, y: 0 })

  const zoomRef = useRef(zoom)
  useEffect(() => {
    zoomRef.current = zoom
  }, [zoom])

  const { data: nodos, isLoading, error, refetch } = useQuery({
    queryKey: ['modulo0', 'organigrama'],
    queryFn: modulo0Service.getOrganigrama,
  })

  const createMutation = useMutation({
    mutationFn: modulo0Service.createNodo,
    onSuccess: () => { 
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal() 
    },
    onError: (err: any) => { setErrorMsg(err.message || 'Error al agregar cargo.') }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<NodoOrganigrama> }) => modulo0Service.updateNodo(id, data),
    onSuccess: () => { 
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal() 
    },
    onError: (err: any) => { setErrorMsg(err.message || 'Error al actualizar cargo.') }
  })

  const deleteMutation = useMutation({
    mutationFn: modulo0Service.deleteNodo,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['modulo0'] }) },
    onError: (err: any) => { alert(err.message || 'No se puede eliminar: el cargo posee subordinados directos.') }
  })

  const importBaseOrgMutation = useMutation({
    mutationFn: async () => {
      const gerencia = await modulo0Service.createNodo({
        nombre_cargo: 'Gerencia General / Representante Legal',
        area: 'Dirección General',
        padre_id: null,
        orden: 0
      })
      const respSST = await modulo0Service.createNodo({
        nombre_cargo: 'Responsable del SG-SST',
        area: 'Seguridad y Salud en el Trabajo',
        padre_id: gerencia.id,
        orden: 0
      })
      await modulo0Service.createNodo({
        nombre_cargo: 'COPASST / Vigía de SST',
        area: 'Comités Paritarios',
        padre_id: gerencia.id,
        orden: 1
      })
      await modulo0Service.createNodo({
        nombre_cargo: 'Comité de Convivencia Laboral',
        area: 'Comités Especiales',
        padre_id: gerencia.id,
        orden: 2
      })
      const operaciones = await modulo0Service.createNodo({
        nombre_cargo: 'Dirección / Jefatura de Operaciones',
        area: 'Operaciones',
        padre_id: gerencia.id,
        orden: 3
      })
      await modulo0Service.createNodo({
        nombre_cargo: 'Brigada de Emergencias y Primeros Auxilios',
        area: 'Seguridad y Salud en el Trabajo',
        padre_id: respSST.id,
        orden: 0
      })
      await modulo0Service.createNodo({
        nombre_cargo: 'Supervisores de Campo y Operaciones',
        area: 'Operaciones',
        padre_id: operaciones.id,
        orden: 0
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
    }
  })

  const buildTree = (flatList: NodoOrganigrama[]): TreeNode[] => {
    const map = new Map<string, TreeNode>()
    const roots: TreeNode[] = []
    flatList.forEach((nodo) => { map.set(nodo.id, { ...nodo, children: [] }) })
    flatList.forEach((nodo) => {
      const node = map.get(nodo.id)!
      if (nodo.padre_id && map.has(nodo.padre_id)) { map.get(nodo.padre_id)!.children.push(node) }
      else { roots.push(node) }
    })
    map.forEach((node) => { node.children.sort((a, b) => a.orden - b.orden) })
    return roots.sort((a, b) => a.orden - b.orden)
  }

  // Get hierarchical level of a node
  const getNodeLevel = useCallback((id: string): number => {
    if (!nodos) return 1
    const map = new Map<string, NodoOrganigrama>()
    nodos.forEach(n => map.set(n.id, n))
    
    let level = 1
    let current = map.get(id)
    while (current && current.padre_id && map.has(current.padre_id)) {
      level++
      current = map.get(current.padre_id)
    }
    return level
  }, [nodos])

  // Get color styles based on node level (used on light theme card borders and badges)
  const getLevelColors = (level: number) => {
    switch(level) {
      case 1:
        return {
          badge: 'bg-amber-50 text-amber-600 border border-amber-200/60',
          accent: 'bg-amber-500',
          glow: 'hover:shadow-[0_0_15px_rgba(245,158,11,0.08)]'
        }
      case 2:
        return {
          badge: 'bg-blue-50 text-blue-600 border border-blue-200/60',
          accent: 'bg-blue-500',
          glow: 'hover:shadow-[0_0_15px_rgba(59,130,246,0.08)]'
        }
      case 3:
        return {
          badge: 'bg-emerald-50 text-emerald-600 border border-emerald-200/60',
          accent: 'bg-emerald-500',
          glow: 'hover:shadow-[0_0_15px_rgba(16,185,129,0.08)]'
        }
      default:
        return {
          badge: 'bg-slate-100 text-slate-700 border border-slate-200',
          accent: 'bg-slate-600',
          glow: 'hover:shadow-[0_0_15px_rgba(139,92,246,0.08)]'
        }
    }
  }

  // Calculate layout of positions recursively
  const calculateAutoPositions = useCallback((flatList: NodoOrganigrama[]): Record<string, { x: number; y: number }> => {
    const newPositions: Record<string, { x: number; y: number }> = {}
    if (flatList.length === 0) return newPositions

    const map = new Map<string, NodoOrganigrama & { children: string[] }>()
    flatList.forEach(n => map.set(n.id, { ...n, children: [] }))
    
    const roots: string[] = []
    flatList.forEach(n => {
      if (n.padre_id && map.has(n.padre_id)) {
        map.get(n.padre_id)!.children.push(n.id)
      } else {
        roots.push(n.id)
      }
    })

    map.forEach(n => {
      n.children.sort((a, b) => {
        const nodeA = map.get(a)
        const nodeB = map.get(b)
        return (nodeA?.orden || 0) - (nodeB?.orden || 0)
      })
    })

    const HORIZONTAL_GAP = 260
    const VERTICAL_GAP = 160
    const nextXAtLevel: Record<number, number> = {}

    const layoutNode = (id: string, depth: number): number => {
      const node = map.get(id)
      if (!node) return 0

      const level = depth + 1
      const y = depth * VERTICAL_GAP + 60

      let x = 0
      if (node.children.length === 0) {
        const currentNextX = nextXAtLevel[level] || 100
        x = currentNextX
        nextXAtLevel[level] = currentNextX + HORIZONTAL_GAP
      } else {
        const childXs = node.children.map(childId => layoutNode(childId, depth + 1))
        const childrenCenter = (childXs[0] + childXs[childXs.length - 1]) / 2
        const currentNextX = nextXAtLevel[level] || 100

        if (childrenCenter < currentNextX) {
          const shift = currentNextX - childrenCenter
          const shiftSubtree = (nodeId: string) => {
            if (newPositions[nodeId]) {
              newPositions[nodeId].x += shift
            }
            const n = map.get(nodeId)
            if (n) n.children.forEach(shiftSubtree)
          }
          node.children.forEach(shiftSubtree)
          
          for (let l = level + 1; l < 20; l++) {
            if (nextXAtLevel[l] !== undefined) {
              nextXAtLevel[l] += shift
            }
          }
          x = currentNextX
          nextXAtLevel[level] = currentNextX + HORIZONTAL_GAP
        } else {
          x = childrenCenter
          nextXAtLevel[level] = Math.max(nextXAtLevel[level] || 100, x + HORIZONTAL_GAP)
        }
      }

      newPositions[id] = { x, y }
      return x
    }

    roots.sort((a, b) => (map.get(a)?.orden || 0) - (map.get(b)?.orden || 0))
    roots.forEach(rootId => layoutNode(rootId, 0))

    return newPositions
  }, [])

  // Auto-fit to screen function
  const fitToScreen = useCallback((currentPositions = positions) => {
    if (!nodos || nodos.length === 0 || Object.keys(currentPositions).length === 0) return
    const container = containerRef.current
    if (!container) return

    const containerWidth = container.clientWidth || 800
    const containerHeight = container.clientHeight || 500

    let minX = Infinity, maxX = -Infinity
    let minY = Infinity, maxY = -Infinity

    nodos.forEach(nodo => {
      const pos = currentPositions[nodo.id] || { x: 0, y: 0 }
      if (pos.x < minX) minX = pos.x
      if (pos.x > maxX) maxX = pos.x
      if (pos.y < minY) minY = pos.y
      if (pos.y > maxY) maxY = pos.y
    })

    const cardWidth = 220
    const cardHeight = 88

    const contentWidth = (maxX - minX) + cardWidth
    const contentHeight = (maxY - minY) + cardHeight

    const padding = 50
    const scaleX = (containerWidth - padding * 2) / contentWidth
    const scaleY = (containerHeight - padding * 2) / contentHeight
    let newZoom = Math.min(scaleX, scaleY)
    
    newZoom = Math.max(0.35, Math.min(1.2, newZoom))

    const centerX = (containerWidth - contentWidth * newZoom) / 2 - minX * newZoom
    const centerY = (containerHeight - contentHeight * newZoom) / 2 - minY * newZoom

    setZoom(newZoom)
    setPan({ x: centerX, y: centerY })
  }, [nodos, positions])

  const hasLoadedRef = useRef(false)
  useEffect(() => {
    if (nodos && nodos.length > 0 && !hasLoadedRef.current) {
      hasLoadedRef.current = true
      const stored = localStorage.getItem('organigrama_positions')
      let initialPositions: Record<string, { x: number; y: number }> = {}
      if (stored) {
        try {
          initialPositions = JSON.parse(stored)
        } catch (e) {
          console.error(e)
        }
      }

      const hasMissingPositions = nodos.some(n => !initialPositions[n.id])
      if (hasMissingPositions) {
        initialPositions = calculateAutoPositions(nodos)
        localStorage.setItem('organigrama_positions', JSON.stringify(initialPositions))
      }

      setPositions(initialPositions)
      
      setTimeout(() => {
        fitToScreen(initialPositions)
      }, 100)
    }
  }, [nodos, calculateAutoPositions, fitToScreen])

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault()
    const zoomFactor = 1.08
    const nextZoom = e.deltaY < 0 ? zoom * zoomFactor : zoom / zoomFactor
    const clampedZoom = Math.min(2.5, Math.max(0.25, nextZoom))
    
    const rect = e.currentTarget.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    
    const canvasMouseX = (mouseX - pan.x) / zoom
    const canvasMouseY = (mouseY - pan.y) / zoom
    
    const newPanX = mouseX - canvasMouseX * clampedZoom
    const newPanY = mouseY - canvasMouseY * clampedZoom
    
    setZoom(clampedZoom)
    setPan({ x: newPanX, y: newPanY })
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.min(2.5, prev + 0.1))
  }
  const handleZoomOut = () => {
    setZoom(prev => Math.max(0.25, prev - 0.1))
  }

  const handleCanvasPanStart = (e: React.MouseEvent) => {
    if (e.button !== 0) return
    if ((e.target as HTMLElement).closest('.interactive-node-element')) return

    isPanningRef.current = true
    panStartPosRef.current = { x: e.clientX, y: e.clientY }
    initialPanRef.current = { ...pan }

    window.addEventListener('mousemove', handleCanvasPanMove)
    window.addEventListener('mouseup', handleCanvasPanEnd)
  }

  const handleCanvasPanMove = useCallback((e: MouseEvent) => {
    if (!isPanningRef.current) return
    const dx = e.clientX - panStartPosRef.current.x
    const dy = e.clientY - panStartPosRef.current.y
    setPan({
      x: initialPanRef.current.x + dx,
      y: initialPanRef.current.y + dy
    })
  }, [])

  const handleCanvasPanEnd = useCallback(() => {
    isPanningRef.current = false
    window.removeEventListener('mousemove', handleCanvasPanMove)
    window.removeEventListener('mouseup', handleCanvasPanEnd)
  }, [handleCanvasPanMove])

  const handleNodeDragStart = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    if (e.button !== 0) return
    if ((e.target as HTMLElement).closest('.interactive-node-element')) return

    const currentPos = positions[nodeId] || { x: 0, y: 0 }
    
    draggedNodeIdRef.current = nodeId
    dragStartPosRef.current = { x: e.clientX, y: e.clientY }
    initialNodePosRef.current = { ...currentPos }
    
    isDraggingNodeRef.current = true
    
    window.addEventListener('mousemove', handleGlobalMouseMove)
    window.addEventListener('mouseup', handleGlobalMouseUp)
  }

  const handleGlobalMouseMove = useCallback((e: MouseEvent) => {
    if (!draggedNodeIdRef.current) return
    
    const dx = e.clientX - dragStartPosRef.current.x
    const dy = e.clientY - dragStartPosRef.current.y
    
    const deltaX = dx / zoomRef.current
    const deltaY = dy / zoomRef.current
    
    let newX = Math.round((initialNodePosRef.current.x + deltaX) / 10) * 10
    let newY = Math.round((initialNodePosRef.current.y + deltaY) / 10) * 10
    
    setPositions(prev => ({
      ...prev,
      [draggedNodeIdRef.current!]: { x: newX, y: newY }
    }))
  }, [])

  const handleGlobalMouseUp = useCallback(() => {
    if (draggedNodeIdRef.current) {
      setPositions(current => {
        localStorage.setItem('organigrama_positions', JSON.stringify(current))
        return current
      })
    }
    draggedNodeIdRef.current = null
    isDraggingNodeRef.current = false
    window.removeEventListener('mousemove', handleGlobalMouseMove)
    window.removeEventListener('mouseup', handleGlobalMouseUp)
  }, [handleGlobalMouseMove])

  const handleNodeTouchStart = (e: React.TouchEvent, nodeId: string) => {
    e.stopPropagation()
    if ((e.target as HTMLElement).closest('.interactive-node-element')) return

    const touch = e.touches[0]
    const currentPos = positions[nodeId] || { x: 0, y: 0 }
    
    draggedNodeIdRef.current = nodeId
    dragStartPosRef.current = { x: touch.clientX, y: touch.clientY }
    initialNodePosRef.current = { ...currentPos }
    
    isDraggingNodeRef.current = true
    
    const handleTouchMove = (evt: TouchEvent) => {
      const t = evt.touches[0]
      const dx = t.clientX - dragStartPosRef.current.x
      const dy = t.clientY - dragStartPosRef.current.y
      
      let newX = Math.round((initialNodePosRef.current.x + dx / zoomRef.current) / 10) * 10
      let newY = Math.round((initialNodePosRef.current.y + dy / zoomRef.current) / 10) * 10
      
      setPositions(prev => ({
        ...prev,
        [nodeId]: { x: newX, y: newY }
      }))
    }
    
    const handleTouchEnd = () => {
      setPositions(current => {
        localStorage.setItem('organigrama_positions', JSON.stringify(current))
        return current
      })
      draggedNodeIdRef.current = null
      isDraggingNodeRef.current = false
      window.removeEventListener('touchmove', handleTouchMove)
      window.removeEventListener('touchend', handleTouchEnd)
    }
    
    window.addEventListener('touchmove', handleTouchMove, { passive: false })
    window.addEventListener('touchend', handleTouchEnd)
  }

  useEffect(() => {
    return () => {
      window.removeEventListener('mousemove', handleGlobalMouseMove)
      window.removeEventListener('mouseup', handleGlobalMouseUp)
      window.removeEventListener('mousemove', handleCanvasPanMove)
      window.removeEventListener('mouseup', handleCanvasPanEnd)
    }
  }, [handleGlobalMouseMove, handleGlobalMouseUp, handleCanvasPanMove, handleCanvasPanEnd])

  const openAddModal = (parentSelectedId: string | null = null) => {
    setEditingNodo(null)
    setNombreCargo('')
    setArea('')
    setPadreId(parentSelectedId || '')
    setOrden(0)
    setErrorMsg('')
    setModalOpen(true)
  }

  const openEditModal = (nodo: NodoOrganigrama) => {
    setEditingNodo(nodo)
    setNombreCargo(nodo.nombre_cargo)
    setArea(nodo.area || '')
    setPadreId(nodo.padre_id || '')
    setOrden(nodo.orden)
    setErrorMsg('')
    setModalOpen(true)
  }

  const closeModal = () => { 
    setModalOpen(false)
    setEditingNodo(null)
    setErrorMsg('') 
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nombreCargo.trim()) { setErrorMsg('El nombre del cargo es obligatorio.'); return }
    const payload = { nombre_cargo: nombreCargo, area: area || null, padre_id: padreId || null, orden: Number(orden) || 0 }
    if (editingNodo) { updateMutation.mutate({ id: editingNodo.id, data: payload }) }
    else { createMutation.mutate(payload) }
  }

  const handleDelete = (id: string) => {
    if (confirm('¿Está seguro de que desea eliminar este cargo?')) { deleteMutation.mutate(id) }
  }

  const handleToggleCollapse = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    setCollapsedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }))
  }

  const handleAutoOrganize = () => {
    if (!nodos || nodos.length === 0) return
    const calculated = calculateAutoPositions(nodos)
    setPositions(calculated)
    localStorage.setItem('organigrama_positions', JSON.stringify(calculated))
    setTimeout(() => {
      fitToScreen(calculated)
    }, 100)
  }

  const handleInlineEditStart = (e: React.MouseEvent, node: NodoOrganigrama) => {
    e.stopPropagation()
    setInlineEditingId(node.id)
    setInlineEditValue(node.nombre_cargo)
  }

  const handleInlineEditSave = (nodeId: string) => {
    if (!inlineEditValue.trim()) {
      setInlineEditingId(null)
      return
    }
    const original = nodos?.find(n => n.id === nodeId)
    if (original && original.nombre_cargo !== inlineEditValue) {
      updateMutation.mutate({
        id: nodeId,
        data: {
          nombre_cargo: inlineEditValue,
          area: original.area,
          padre_id: original.padre_id,
          orden: original.orden
        }
      })
    }
    setInlineEditingId(null)
  }

  const isNodeVisible = useCallback((nodeId: string, flatList: NodoOrganigrama[]): boolean => {
    const map = new Map<string, NodoOrganigrama>()
    flatList.forEach(n => map.set(n.id, n))
    
    let current = map.get(nodeId)
    while (current && current.padre_id) {
      if (collapsedNodes[current.padre_id]) {
        return false
      }
      current = map.get(current.padre_id)
    }
    return true
  }, [collapsedNodes])

  const isDescendant = (childId: string, parentId: string): boolean => {
    if (!nodos) return false
    const map = new Map<string, NodoOrganigrama>()
    nodos.forEach(n => map.set(n.id, n))
    
    let current = map.get(childId)
    while (current && current.padre_id) {
      if (current.padre_id === parentId) return true
      current = map.get(current.padre_id)
    }
    return false
  }

  const visibleNodes = nodos ? nodos.filter(n => isNodeVisible(n.id, nodos)) : []
  const visibleConnectors = nodos ? nodos.filter(n => {
    if (!n.padre_id) return false
    const parentExists = nodos.some(p => p.id === n.padre_id)
    if (!parentExists) return false
    return isNodeVisible(n.id, nodos) && isNodeVisible(n.padre_id, nodos)
  }) : []

  const hasChildren = (nodeId: string) => {
    if (!nodos) return false
    return nodos.some(n => n.padre_id === nodeId)
  }

  // Handle high quality printing in new landscape tab/window
  const handlePrint = () => {
    if (!nodos || nodos.length === 0) return

    let minX = Infinity, maxX = -Infinity
    let minY = Infinity, maxY = -Infinity

    nodos.forEach(nodo => {
      const pos = positions[nodo.id] || { x: 100, y: 100 }
      if (pos.x < minX) minX = pos.x
      if (pos.x > maxX) maxX = pos.x
      if (pos.y < minY) minY = pos.y
      if (pos.y > maxY) maxY = pos.y
    })

    const cardWidth = 220
    const cardHeight = 88
    const padding = 40

    const width = (maxX - minX) + cardWidth
    const height = (maxY - minY) + cardHeight

    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      alert('Por favor permite las ventanas emergentes para poder imprimir el organigrama.')
      return
    }

    const svgConnectors = visibleConnectors.map(node => {
      const pPos = positions[node.padre_id!] || { x: 0, y: 0 }
      const cPos = positions[node.id] || { x: 0, y: 0 }
      
      const pX = pPos.x - minX + padding
      const pY = pPos.y - minY + padding
      const cX = cPos.x - minX + padding
      const cY = cPos.y - minY + padding

      const startX = pX + 110
      const startY = pY + 88
      const endX = cX + 110
      const endY = cY - 5
      const midY = (startY + endY) / 2

      return `<path d="M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}" fill="none" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)" />`
    }).join('\n')

    const nodesHtml = visibleNodes.map(node => {
      const pos = positions[node.id] || { x: 100, y: 100 }
      const nX = pos.x - minX + padding
      const nY = pos.y - minY + padding
      const lvl = getNodeLevel(node.id)

      let accentColor = '#6b7280'
      let badgeBg = '#f3f4f6'
      let badgeText = '#374151'
      let badgeBorder = '#e5e7eb'

      if (lvl === 1) {
        accentColor = '#f59e0b'
        badgeBg = '#fef3c7'
        badgeText = '#d97706'
        badgeBorder = '#fde68a'
      } else if (lvl === 2) {
        accentColor = '#3b82f6'
        badgeBg = '#dbeafe'
        badgeText = '#2563eb'
        badgeBorder = '#bfdbfe'
      } else if (lvl === 3) {
        accentColor = '#10b981'
        badgeBg = '#d1fae5'
        badgeText = '#059669'
        badgeBorder = '#a7f3d0'
      } else {
        accentColor = '#8b5cf6'
        badgeBg = '#f3e8ff'
        badgeText = '#7c3aed'
        badgeBorder = '#e9d5ff'
      }

      return `
        <div class="node-card" style="left: ${nX}px; top: ${nY}px; border-color: ${accentColor}80;">
          <div class="accent-stripe" style="background-color: ${accentColor};"></div>
          <div style="display: flex; justify-content: space-between; align-items: start; margin-left: 6px;">
            <span class="text-area">${node.area || 'Sin Área'}</span>
            <span class="badge" style="background-color: ${badgeBg}; color: ${badgeText}; border-color: ${badgeBorder};">Nivel ${lvl}</span>
          </div>
          <div style="margin-left: 6px; margin-top: 4px;">
            <div class="text-title">${node.nombre_cargo}</div>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-left: 6px; margin-top: 4px;">
            <span class="text-ord">Ord: <strong>${node.orden}</strong></span>
          </div>
        </div>
      `
    }).join('\n')

    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Organigrama - Impresión</title>
        <meta charset="utf-8" />
        <style>
          @page {
            size: landscape;
            margin: 10mm;
          }
          @media print {
            body {
              background: white !important;
              color: black !important;
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
            }
          }
          body {
            margin: 0;
            padding: 20px;
            background: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          }
          .print-canvas {
            position: relative;
            width: ${width + padding * 2}px;
            height: ${height + padding * 2}px;
            background: white;
          }
          .node-card {
            position: absolute;
            width: 220px;
            height: 88px;
            border-radius: 12px;
            border: 1.5px solid #cbd5e1;
            background: white !important;
            padding: 12px 14px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            page-break-inside: avoid;
          }
          .accent-stripe {
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            width: 5px;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
          }
          .badge {
            font-size: 9px;
            font-weight: bold;
            padding: 1px 5px;
            border-radius: 4px;
            border-width: 1px;
            border-style: solid;
          }
          .text-title {
            font-size: 12px;
            font-weight: bold;
            color: #1e293b;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .text-area {
            font-size: 9px;
            font-weight: bold;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .text-ord {
            font-size: 9px;
            color: #64748b;
          }
          .text-ord strong {
            color: #334155;
          }
        </style>
      </head>
      <body>
        <div class="print-canvas">
          <svg style="position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; pointer-events: none;">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
              >
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#cbd5e1" />
              </marker>
            </defs>
            ${svgConnectors}
          </svg>
          ${nodesHtml}
        </div>
        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
              window.close();
            }, 300);
          }
        </script>
      </body>
      </html>
    `

    printWindow.document.open()
    printWindow.document.write(htmlContent)
    printWindow.document.close()
  }

  if (isLoading) {
    return <LoadingSpinner text="Cargando estructura del organigrama..." />
  }

  if (error) {
    return <ErrorDisplay message={(error as any)?.message || 'No se pudo cargar el organigrama'} onRetry={refetch} />
  }

  return (
    <div id="organigrama-root-view" className="flex flex-col h-[calc(100vh-6rem)] min-h-[500px] bg-white border border-slate-200 rounded-2xl relative overflow-hidden font-sans select-none">
      <style>{customStyles}</style>

      {/* TOOLBAR */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 z-10 no-print">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center border border-brand-500/20">
            <GitBranch className="w-5 h-5 text-brand-500" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-800 tracking-wide">Organigrama Funcional</h1>
            <p className="text-xs text-slate-500">Diseño dinámico de la jerarquía de cargos</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl flex items-center gap-2 text-xs font-semibold text-slate-600">
            <Users className="w-4 h-4 text-slate-500" />
            <span>Total: <strong className="text-slate-800">{nodos?.length || 0}</strong> cargos</span>
          </div>

          {(!nodos || nodos.length === 0) && (
            <Button
              variant="secondary"
              onClick={() => importBaseOrgMutation.mutate()}
              disabled={importBaseOrgMutation.isPending}
              className="text-xs py-1.5 h-9 bg-primary-50 hover:bg-primary-100 border border-primary-200 text-primary-500 font-bold"
            >
              {importBaseOrgMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4 text-primary-500" />}
              Cargar Estructura SG-SST
            </Button>
          )}

          <Button variant="primary" onClick={() => openAddModal(null)} className="text-xs py-1.5 h-9">
            <Plus className="w-4 h-4" /> Nuevo Cargo
          </Button>

          <Button variant="ghost" onClick={handleAutoOrganize} className="text-xs py-1.5 h-9 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700">
            <GitBranch className="w-4 h-4 text-slate-500" /> Auto-organizar
          </Button>

          <Button variant="ghost" onClick={handlePrint} className="text-xs py-1.5 h-9 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700">
            <Printer className="w-4 h-4 text-slate-500" /> Imprimir
          </Button>
        </div>
      </div>

      {/* VIEWPORT CANVAS */}
      <div 
        ref={containerRef}
        className="organigrama-viewport-container flex-1 relative overflow-hidden cursor-grab active:cursor-grabbing bg-slate-50"
        onMouseDown={handleCanvasPanStart}
        onWheel={handleWheel}
      >
        <div 
          className="organigrama-canvas absolute w-[10000px] h-[10000px]"
          style={{ 
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: '0 0'
          }}
        >
          {/* SVG CONNECTIONS */}
          <svg className="absolute inset-0 pointer-events-none overflow-visible w-full h-full">
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
              >
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#cbd5e1" />
              </marker>
            </defs>

            {visibleConnectors.map(node => {
              const pPos = positions[node.padre_id!] || { x: 0, y: 0 }
              const cPos = positions[node.id] || { x: 0, y: 0 }
              
              const startX = pPos.x + 110
              const startY = pPos.y + 88
              const endX = cPos.x + 110
              const endY = cPos.y - 5
              
              const midY = (startY + endY) / 2
              
              const pathData = `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`
              
              return (
                <path
                  key={`conn-${node.id}`}
                  d={pathData}
                  fill="none"
                  stroke="#cbd5e1"
                  strokeWidth="2"
                  className="svg-connector-path"
                  markerEnd="url(#arrow)"
                />
              )
            })}
          </svg>

          {/* NODES */}
          {nodos && visibleNodes.map(node => {
            const pos = positions[node.id] || { x: 100, y: 100 }
            const lvl = getNodeLevel(node.id)
            const style = getLevelColors(lvl)
            const isEditing = inlineEditingId === node.id

            return (
              <div
                key={node.id}
                className={`node-card group absolute w-[220px] h-[88px] rounded-2xl border border-slate-200 bg-white hover:border-slate-300 ${style.glow} shadow-sm p-4 flex flex-col justify-between cursor-pointer`}
                style={{ 
                  left: `${pos.x}px`, 
                  top: `${pos.y}px`
                }}
                onMouseDown={(e) => handleNodeDragStart(e, node.id)}
                onTouchStart={(e) => handleNodeTouchStart(e, node.id)}
              >
                {/* Accent stripe */}
                <div className={`absolute top-0 left-0 bottom-0 w-1.5 rounded-l-2xl ${style.accent}`} />

                {/* Header info */}
                <div className="flex justify-between items-start gap-2 pl-1">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider truncate max-w-[120px]">
                    {node.area || 'Sin Área'}
                  </span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md ${style.badge} whitespace-nowrap`}>
                    Nivel {lvl}
                  </span>
                </div>

                {/* Cargo Name */}
                <div className="pl-1 mb-1">
                  {isEditing ? (
                    <input
                      value={inlineEditValue}
                      onChange={(e) => setInlineEditValue(e.target.value)}
                      onBlur={() => handleInlineEditSave(node.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleInlineEditSave(node.id)
                        else if (e.key === 'Escape') setInlineEditingId(null)
                      }}
                      className="w-full bg-white border border-brand-500 text-slate-800 rounded px-2 py-0.5 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-brand-500 interactive-node-element"
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      onMouseDown={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <h3 
                      className="text-xs font-bold text-slate-800 tracking-wide truncate pr-2"
                      title="Doble clic para editar"
                      onDoubleClick={(e) => handleInlineEditStart(e, node)}
                    >
                      {node.nombre_cargo}
                    </h3>
                  )}
                </div>

                {/* Subordinate Toggle / Indicators */}
                <div className="flex justify-between items-center pl-1">
                  <span className="text-[9px] text-slate-500 font-semibold uppercase">
                    Ord: <strong className="text-slate-700">{node.orden}</strong>
                  </span>

                  {hasChildren(node.id) && (
                    <button
                      onClick={(e) => handleToggleCollapse(e, node.id)}
                      className="w-5 h-5 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 hover:border-slate-400 transition-all cursor-pointer shadow-sm interactive-node-element"
                      title={collapsedNodes[node.id] ? 'Expandir subordinados' : 'Colapsar subordinados'}
                    >
                      {collapsedNodes[node.id] ? (
                        <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </button>
                  )}
                </div>

                {/* FLOATING ACTION OVERLAY */}
                <div className="absolute -top-10 right-0 flex items-center gap-1 bg-white border border-slate-200 p-1.5 rounded-xl opacity-0 group-hover:opacity-100 transition-all duration-200 shadow-lg scale-90 origin-bottom-right group-hover:scale-100 pointer-events-none group-hover:pointer-events-auto interactive-node-element no-print">
                  <button
                    onClick={() => openAddModal(node.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
                    title="Agregar subordinado"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => openEditModal(node)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
                    title="Editar cargo"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(node.id)}
                    className="p-1.5 rounded-lg text-red-500 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="Eliminar cargo"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* FLOATING CONTROLS (BOTTOM-RIGHT) */}
      <div className="absolute bottom-6 right-6 flex items-center gap-1.5 bg-white border border-slate-200/80 p-2 rounded-2xl shadow-lg backdrop-blur-md z-10 no-print">
        <button
          onClick={handleZoomIn}
          className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
          title="Acercar (+)"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <span className="text-[10px] font-bold text-slate-500 px-1 select-none min-w-[36px] text-center">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={handleZoomOut}
          className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
          title="Alejar (-)"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <div className="w-[1px] h-6 bg-slate-200 mx-1" />
        <button
          onClick={() => fitToScreen()}
          className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
          title="Ajustar a pantalla"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* MODAL */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 no-print animate-fade-in">
          <Card 
            title={editingNodo ? 'Editar Cargo' : 'Registrar Nuevo Cargo'}
            className="w-full max-w-md bg-white border border-slate-200 shadow-2xl relative overflow-hidden text-slate-800"
            action={
              <button onClick={closeModal} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-all">
                <X className="w-5 h-5" />
              </button>
            }
          >
            <form onSubmit={handleSubmit} className="space-y-4 mt-2">
              {errorMsg && (
                <div className="bg-red-50 border border-red-200 text-red-600 p-3.5 rounded-xl flex items-start gap-2.5 text-xs font-semibold leading-relaxed">
                  <AlertTriangle className="w-4.5 h-4.5 flex-shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <FormField label="Nombre del Cargo *">
                <Input
                  value={nombreCargo}
                  onChange={(e) => setNombreCargo(e.target.value)}
                  placeholder="Ej. Director de Operaciones"
                  className="bg-white border-slate-200 text-slate-850 rounded-xl focus:border-brand-500 focus:ring-brand-500"
                  required
                />
              </FormField>

              <FormField label="Área / Departamento">
                <Input
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  placeholder="Ej. Recursos Humanos"
                  className="bg-white border-slate-200 text-slate-850 rounded-xl focus:border-brand-500 focus:ring-brand-500"
                />
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-slate-500 pl-0.5">Cargo Superior (Padre)</label>
                  <select
                    value={padreId}
                    onChange={(e) => setPadreId(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="">Ninguno (Raíz)</option>
                    {nodos && nodos
                      .filter(n => !editingNodo || (n.id !== editingNodo.id && !isDescendant(n.id, editingNodo.id)))
                      .map(n => (
                        <option key={n.id} value={n.id}>
                          {n.nombre_cargo} ({n.area || 'Sin Área'})
                        </option>
                      ))}
                  </select>
                </div>

                <FormField label="Orden de visualización">
                  <Input
                    type="number"
                    value={orden}
                    onChange={(e) => setOrden(Number(e.target.value) || 0)}
                    min={0}
                    className="bg-white border-slate-200 text-slate-850 rounded-xl focus:border-brand-500 focus:ring-brand-500"
                  />
                </FormField>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 mt-6">
                <Button variant="ghost" onClick={closeModal} className="text-xs py-2 h-10 hover:bg-slate-100 text-slate-700">
                  Cancelar
                </Button>
                <Button variant="primary" type="submit" className="text-xs py-2 h-10" disabled={createMutation.isPending || updateMutation.isPending}>
                  {editingNodo ? 'Guardar Cambios' : 'Registrar Cargo'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}