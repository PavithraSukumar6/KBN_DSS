import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Users, Briefcase, Clock, AlertTriangle, CheckCircle,
    ArrowRight, Activity, Filter
} from 'lucide-react';

const WorkloadManager = () => {
    const [stats, setStats] = useState(null);
    const [queue, setQueue] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDocs, setSelectedDocs] = useState([]);
    const [assignTo, setAssignTo] = useState('');

    // Filter State
    const [filterStatus, setFilterStatus] = useState('');
    const [filterPriority, setFilterPriority] = useState('');

    useEffect(() => {
        fetchData();
        fetchQueue();
    }, []);

    const fetchData = async () => {
        try {
            const [statsRes, usersRes] = await Promise.all([
                axios.get('http://localhost:5000/workload/stats'),
                axios.get('http://localhost:5000/users')
            ]);
            setStats(statsRes.data);
            setUsers(usersRes.data);
        } catch (err) {
            console.error("Failed to load workload data", err);
        }
    };

    const fetchQueue = async () => {
        setLoading(true);
        try {
            // Fetch all documents, then we filter client side or backend
            // Using existing /documents endpoint
            const res = await axios.get('http://localhost:5000/documents?is_admin=true');
            setQueue(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAssign = async () => {
        if (!assignTo || selectedDocs.length === 0) return;
        try {
            await axios.post('http://localhost:5000/workload/assign', {
                doc_ids: selectedDocs,
                user_id: assignTo,
                assigner: 'Admin'
            });
            alert("Documents Assigned Successfully");
            setSelectedDocs([]);
            setAssignTo('');
            fetchData();
            fetchQueue();
        } catch (err) {
            alert("Assignment Failed");
        }
    };

    const getFilteredQueue = () => {
        let items = queue;
        if (filterStatus) items = items.filter(d => d.ocr_status === filterStatus);
        if (filterPriority) items = items.filter(d => d.priority === filterPriority);

        // Default sort by SLA Risk (Overdue first), then Priority, then Date
        return items.sort((a, b) => {
            // Custom sort logic
            if (a.sla_status === 'Overdue' && b.sla_status !== 'Overdue') return -1;
            if (b.sla_status === 'Overdue' && a.sla_status !== 'Overdue') return 1;

            // Priority map
            const pMap = { 'Urgent': 3, 'High': 2, 'Medium': 1, 'Low': 0 };
            const pa = pMap[a.priority] || 0;
            const pb = pMap[b.priority] || 0;
            if (pa !== pb) return pb - pa;

            return new Date(b.upload_date) - new Date(a.upload_date);
        });
    };

    const toggleSelect = (id) => {
        if (selectedDocs.includes(id)) {
            setSelectedDocs(prev => prev.filter(d => d !== id));
        } else {
            setSelectedDocs(prev => [...prev, id]);
        }
    };

    if (!stats) return <div className="p-8">Loading Workload Engine...</div>;

    const filteredItems = getFilteredQueue();

    return (
        <div className="glass-panel" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Briefcase size={24} /> Workload Manager
                </h2>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn btn-ghost" onClick={fetchData}>
                        <Activity size={18} /> Refresh Stats
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
                <div className="stat-card" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                    <h3 style={{ fontSize: '0.9rem', color: '#60a5fa', marginBottom: '0.5rem' }}>QC Pending</h3>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                        {stats.status_distribution?.['Completed'] || 0}
                    </div>
                </div>
                <div className="stat-card" style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                    <h3 style={{ fontSize: '0.9rem', color: '#4ade80', marginBottom: '0.5rem' }}>QC Passed</h3>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                        {stats.status_distribution?.['QC_Passed'] || 0}
                    </div>
                </div>
                <div className="stat-card" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                    <h3 style={{ fontSize: '0.9rem', color: '#f87171', marginBottom: '0.5rem' }}>Overdue SLA</h3>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                        {stats.sla_status?.['Overdue'] || 0}
                    </div>
                </div>
                <div className="stat-card" style={{ background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                    <h3 style={{ fontSize: '0.9rem', color: '#facc15', marginBottom: '0.5rem' }}>Rigorous QC Req.</h3>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                        {stats.status_distribution?.['Rigorous_QC'] || 0}
                    </div>
                </div>
            </div>

            {/* Assignment Bar */}
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>{selectedDocs.length} documents selected</span>
                <select className="input" value={assignTo} onChange={e => setAssignTo(e.target.value)} style={{ minWidth: '200px' }}>
                    <option value="">-- Assign to User --</option>
                    {users.map(u => (
                        <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
                    ))}
                </select>
                <button className="btn" onClick={handleAssign} disabled={!assignTo || selectedDocs.length === 0}>
                    Assign Work
                </button>
            </div>

            {/* Queue Table */}
            <div className="table-container">
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            <th style={{ width: '40px' }}><input type="checkbox" onChange={(e) => {
                                if (e.target.checked) setSelectedDocs(filteredItems.map(d => d.id));
                                else setSelectedDocs([]);
                            }} /></th>
                            <th style={{ textAlign: 'left' }}>Document</th>
                            <th>Status</th>
                            <th>Priority</th>
                            <th>Assigned To</th>
                            <th>SLA Status</th>
                            <th>Due Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredItems.map(doc => (
                            <tr key={doc.id} style={{ borderBottom: '1px solid var(--glass-border)' }}>
                                <td>
                                    <input
                                        type="checkbox"
                                        checked={selectedDocs.includes(doc.id)}
                                        onChange={() => toggleSelect(doc.id)}
                                    />
                                </td>
                                <td>
                                    <div style={{ color: 'white' }}>{doc.filename}</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{doc.category}</div>
                                </td>
                                <td>
                                    <span className={`status-badge ${doc.ocr_status === 'QC_Passed' ? 'status-success' :
                                            doc.ocr_status === 'Rigorous_QC' ? 'status-warning' :
                                                'status-neutral'
                                        }`}>
                                        {doc.ocr_status}
                                    </span>
                                </td>
                                <td>
                                    <span style={{
                                        color: doc.priority === 'Urgent' ? '#ef4444' : doc.priority === 'High' ? '#f97316' : 'inherit',
                                        fontWeight: doc.priority === 'Urgent' ? 'bold' : 'normal'
                                    }}>
                                        {doc.priority || 'Medium'}
                                    </span>
                                </td>
                                <td>
                                    {doc.assigned_to ? (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <Users size={14} /> {doc.assigned_to}
                                        </div>
                                    ) : (
                                        <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Unassigned</span>
                                    )}
                                </td>
                                <td>
                                    {doc.sla_status === 'Overdue' && (
                                        <span style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                                            <AlertTriangle size={14} /> Overdue
                                        </span>
                                    )}
                                    {doc.sla_status === 'On Track' && <span style={{ color: '#4ade80' }}>On Track</span>}
                                    {!doc.sla_status && '-'}
                                </td>
                                <td>
                                    {doc.sla_due_date ? new Date(doc.sla_due_date).toLocaleDateString() : '-'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default WorkloadManager;
