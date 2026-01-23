import React, { useState, useRef, useEffect } from 'react';
import './ResizablePanel.css';

interface ResizablePanelProps {
  children: React.ReactNode;
  direction: 'horizontal' | 'vertical';
  minSize?: number;
  maxSize?: number;
  defaultSize?: number;
  storageKey?: string;
  className?: string;
  edge?: 'left' | 'right' | 'top' | 'bottom';
}

export const ResizablePanel: React.FC<ResizablePanelProps> = ({
  children,
  direction,
  minSize = 100,
  maxSize = 1000,
  defaultSize,
  storageKey,
  className = '',
  edge,
}) => {
  const [size, setSize] = useState(() => {
    if (storageKey) {
      const saved = localStorage.getItem(storageKey);
      if (saved) return parseInt(saved, 10);
    }
    return defaultSize || (direction === 'horizontal' ? 200 : 240);
  });

  const [isDragging, setIsDragging] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const startPosRef = useRef(0);
  const startSizeRef = useRef(0);

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(storageKey, size.toString());
    }
  }, [size, storageKey]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startPosRef.current = direction === 'horizontal' ? e.clientY : e.clientX;
    startSizeRef.current = size;
    document.body.style.cursor = direction === 'horizontal' ? 'row-resize' : 'col-resize';
    document.body.style.userSelect = 'none';
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const delta = direction === 'horizontal'
        ? e.clientY - startPosRef.current
        : e.clientX - startPosRef.current;
      
      const newSize = startSizeRef.current + delta;
      const clampedSize = Math.max(minSize, Math.min(maxSize, newSize));
      setSize(clampedSize);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, direction, minSize, maxSize]);

  const style: React.CSSProperties = direction === 'horizontal'
    ? {
        height: `${size}px`,
        width: '100%',
        flexShrink: 0,
      }
    : {
        width: `${size}px`,
        flexShrink: 0,
      };

  const handleClass = direction === 'horizontal' 
    ? 'resize-handle-horizontal'
    : `resize-handle-vertical ${edge === 'left' ? 'resize-handle-left' : 'resize-handle-right'}`;

  return (
    <div
      ref={panelRef}
      className={`resizable-panel resizable-panel-${direction} ${className}`}
      style={style}
    >
      {children}
      <div
        className={`resize-handle ${handleClass} ${isDragging ? 'resize-handle-active' : ''}`}
        onMouseDown={handleMouseDown}
      />
    </div>
  );
};

