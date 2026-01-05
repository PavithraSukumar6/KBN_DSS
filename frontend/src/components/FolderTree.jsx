import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Folder, FolderOpen, Box } from 'lucide-react';

const FolderNode = ({ node, containers, onSelect, selectedId, level = 0 }) => {
    const [isOpen, setIsOpen] = useState(level === 0); // Root open by default
    const children = containers.filter(c => c.parent_id === node.id);
    const isSelected = selectedId === node.id;

    const handleToggle = (e) => {
        e.stopPropagation();
        setIsOpen(!isOpen);
    };

    return (
        <div style={{ marginLeft: `${level * 16}px` }}>
            <div
                className={`folder-item ${isSelected ? 'active' : ''}`}
                onClick={() => onSelect(node.id)}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                    color: isSelected ? '#60a5fa' : 'var(--text-muted)'
                }}
            >
                {children.length > 0 ? (
                    <span onClick={handleToggle} style={{ display: 'flex', alignItems: 'center' }}>
                        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </span>
                ) : (
                    <span style={{ width: '16px' }} />
                )}

                {isOpen ? <FolderOpen size={18} className="folder-icon" /> : <Folder size={18} className="folder-icon" />}
                <span style={{ fontSize: '0.9rem', fontWeight: isSelected ? '600' : '400' }}>
                    {node.name || node.id}
                </span>
            </div>

            {isOpen && children.length > 0 && (
                <div className="folder-children">
                    {children.map(child => (
                        <FolderNode
                            key={child.id}
                            node={child}
                            containers={containers}
                            onSelect={onSelect}
                            selectedId={selectedId}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}

            <style>{`
                .folder-item:hover {
                    background: rgba(255,255,255,0.05);
                    color: white;
                }
                .folder-item.active {
                    color: #60a5fa;
                }
                .folder-icon {
                    color: #fbbf24;
                }
            `}</style>
        </div>
    );
};

const FolderTree = ({ containers = [], onSelect, selectedId }) => {
    // Find root nodes (those with no parent or parent 'ROOT' if we start from KBN)
    const roots = (containers || []).filter(c => !c.parent_id || c.id === 'ROOT');

    return (
        <div className="folder-tree" style={{ userSelect: 'none' }}>
            {roots.map(root => (
                <FolderNode
                    key={root.id}
                    node={root}
                    containers={containers}
                    onSelect={onSelect}
                    selectedId={selectedId}
                />
            ))}
        </div>
    );
};

export default FolderTree;
