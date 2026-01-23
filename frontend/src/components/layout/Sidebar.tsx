import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './Sidebar.css';

interface ProjectItem {
  id: string;
  name: string;
  type: 'project' | 'model' | 'simulation';
  children?: ProjectItem[];
}

interface TreeNodeProps {
  item: ProjectItem;
  level: number;
  isExpanded: boolean;
  onToggle: (id: string) => void;
  onSelect: (id: string) => void;
  selectedId?: string;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  item,
  level,
  isExpanded,
  onToggle,
  onSelect,
  selectedId,
}) => {
  const hasChildren = item.children && item.children.length > 0;
  const isSelected = selectedId === item.id;

  return (
    <div>
      <div
        className={`tree-node ${isSelected ? 'tree-node-selected' : ''}`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={() => {
          if (hasChildren) {
            onToggle(item.id);
          }
          onSelect(item.id);
        }}
      >
        {hasChildren && (
          <span className="tree-node-icon">{isExpanded ? '▼' : '▶'}</span>
        )}
        {!hasChildren && <span className="tree-node-icon-spacer" />}
        <span className="tree-node-icon-type">{getIcon(item.type)}</span>
        <span className="tree-node-label">{item.name}</span>
      </div>
      {hasChildren && isExpanded && (
        <div>
          {item.children!.map((child) => (
            <TreeNode
              key={child.id}
              item={child}
              level={level + 1}
              isExpanded={isExpanded}
              onToggle={onToggle}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  );
};

function getIcon(type: string): string {
  switch (type) {
    case 'project':
      return '□';
    case 'model':
      return '◊';
    case 'simulation':
      return '△';
    default:
      return '○';
  }
}

export const Sidebar: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInstances = async () => {
      try {
        setLoading(true);
        const response = await api.get('/antenna-instances/');
        const instances = response.data || [];
        
        // Convert instances to project structure
        const projectItems: ProjectItem[] = [
          {
            id: 'root',
            name: 'Antenna Instances',
            type: 'project',
            children: instances.map((inst: any) => ({
              id: inst.instance_id,
              name: `${inst.instance_id} - ${inst.parameters?.frequency_band || '2.4GHz'}`,
              type: 'project' as const,
            })),
          },
        ];
        
        setProjects(projectItems);
        if (projectItems[0]?.children && projectItems[0].children.length > 0) {
          setExpandedIds(new Set(['root']));
          setSelectedId(projectItems[0].children[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch antenna instances:', err);
        // Use empty structure on error
        setProjects([{
          id: 'root',
          name: 'Antenna Instances',
          type: 'project',
          children: [],
        }]);
      } finally {
        setLoading(false);
      }
    };

    fetchInstances();
  }, []);

  const handleToggle = (id: string) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Projects</h2>
      </div>
      <div className="sidebar-content">
        {loading ? (
          <div className="sidebar-loading">Loading...</div>
        ) : projects.length === 0 ? (
          <div className="sidebar-empty">No antenna instances</div>
        ) : (
          projects.map((project) => (
            <TreeNode
              key={project.id}
              item={project}
              level={0}
              isExpanded={expandedIds.has(project.id)}
              onToggle={handleToggle}
              onSelect={setSelectedId}
              selectedId={selectedId}
            />
          ))
        )}
      </div>
    </div>
  );
};
















