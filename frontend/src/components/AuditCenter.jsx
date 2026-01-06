import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, AlertTriangle, Eye, Search, FileText, Download, User } from 'lucide-react';

const AuditCenter = ({ currentUser }) => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [reportLoading, setReportLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('raw_logs'); // or 'reports'
    const [reportData, setReportData] = useState([]);
    const [filters, setFilters] = useState({
        user: '',
        action: '',
        start_date: '',
        end_date: ''
    });

    useEffect(() => {
        fetchLogs();
    }, [filters]);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams(filters);
            const res = await axios.get(`http://localhost:5000/audit/logs?${params.toString()}`);
            setLogs(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchRestrictedReport = async () => {
        setReportLoading(true);
        try {
            // Default 30 days
            const res = await axios.get('http://localhost:5000/audit/reports/restricted?days=30');
            setReportData(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setReportLoading(false);
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Shield size={24} color="#60a5fa" /> Audit & Security Center
                </h2>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button
                        className={`btn ${activeTab === 'raw_logs' ? '' : 'btn-ghost'}`}
                        onClick={() => setActiveTab('raw_logs')}
                    >
                        Detailed Logs
                    </button>
                    <button
                        className={`btn ${activeTab === 'reports' ? '' : 'btn-ghost'}`}
                        onClick={() => { setActiveTab('reports'); fetchRestrictedReport(); }}
                    >
                        Security Reports
                    </button>
                </div>
            </div>

            {activeTab === 'raw_logs' && (
                <div>
                    {/* Filters */}
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
                        <input
                            className="input"
                            placeholder="Filter by User..."
                            value={filters.user}
                            onChange={e => setFilters({ ...filters, user: e.target.value })}
                        />
                        <select
                            className="input"
                            value={filters.action}
                            onChange={e => setFilters({ ...filters, action: e.target.value })}
                        >
                            <option value="">All Actions</option>
                            <option value="VIEW">View Document</option>
                            <option value="VIEW_RESTRICTED">View Restricted</option>
                            <option value="UPLOAD">Upload</option>
                            <option value="SEARCH_ZERO_RESULTS">Zero Result Search</option>
                            <option value="reclassify">Metadata Change</option>
                        </select>
                        <input
                            type="date"
                            className="input"
                            value={filters.start_date}
                            onChange={e => setFilters({ ...filters, start_date: e.target.value })}
                        />
                    </div>

                    <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead style={{ position: 'sticky', top: 0, background: '#1e293b' }}>
                                <tr style={{ borderBottom: '1px solid var(--glass-border)', textAlign: 'left' }}>
                                    <th style={{ padding: '1rem' }}>Time</th>
                                    <th style={{ padding: '1rem' }}>User</th>
                                    <th style={{ padding: '1rem' }}>Action</th>
                                    <th style={{ padding: '1rem' }}>Details</th>
                                    <th style={{ padding: '1rem' }}>Entity</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? <tr><td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>Loading logs...</td></tr> :
                                    logs.map(log => (
                                        <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{log.timestamp}</td>
                                            <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#60a5fa' }}>
                                                {log.performed_by}
                                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>{log.ip_address || 'N/A'}</div>
                                            </td>
                                            <td style={{ padding: '0.75rem' }}>
                                                <span style={{
                                                    padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem',
                                                    background: log.action.includes('RESTRICTED') || log.action.includes('ZERO') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.1)',
                                                    color: log.action.includes('RESTRICTED') || log.action.includes('ZERO') ? '#f87171' : '#4ade80'
                                                }}>
                                                    {log.action}
                                                </span>
                                            </td>
                                            <td style={{ padding: '0.75rem', fontSize: '0.9rem' }}>
                                                {log.scope && <span style={{ marginRight: '0.5rem', padding: '1px 4px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '3px', fontSize: '0.7rem' }}>{log.scope}</span>}
                                                {log.details}
                                                {/* Show diffs if available */}
                                                {log.old_value && (
                                                    <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '4px' }}>
                                                        <div style={{ color: '#f87171' }}>- {log.old_value}</div>
                                                        <div style={{ color: '#4ade80' }}>+ {log.new_value}</div>
                                                    </div>
                                                )}
                                            </td>
                                            <td style={{ padding: '0.75rem', fontSize: '0.8rem' }}>{log.entity_type} #{log.entity_id}</td>
                                        </tr>
                                    ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {activeTab === 'reports' && (
                <div>
                    <h3 style={{ marginBottom: '1rem' }}>Restricted Access Report (Last 30 Days)</h3>
                    {/* Report Chart or Table */}
                    {reportLoading ? <p>Loading Report...</p> : (
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: 'rgba(255,255,255,0.05)' }}>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Time</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>User</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Document</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Confidentiality</th>
                                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reportData.length === 0 ? <tr><td colSpan="5" style={{ padding: '1rem', textAlign: 'center' }}>No restricted access events found.</td></tr> :
                                    reportData.map(row => (
                                        <tr key={row.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <td style={{ padding: '0.5rem' }}>{row.timestamp}</td>
                                            <td style={{ padding: '0.5rem', color: '#60a5fa' }}>{row.performed_by}</td>
                                            <td style={{ padding: '0.5rem' }}>{row.filename}</td>
                                            <td style={{ padding: '0.5rem' }}><span style={{ color: '#f87171' }}>{row.confidentiality_level}</span></td>
                                            <td style={{ padding: '0.5rem' }}>{row.action}</td>
                                        </tr>
                                    ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    );
};

export default AuditCenter;
