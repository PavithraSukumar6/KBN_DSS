import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Plus, Power, Check, AlertCircle } from 'lucide-react';

const GovernanceDashboard = () => {
    const [taxonomy, setTaxonomy] = useState([]);
    const [newValue, setNewValue] = useState('');
    const [category, setCategory] = useState('DocumentType');
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchTaxonomy();
    }, []);

    const fetchTaxonomy = async () => {
        try {
            const res = await axios.get('http://localhost:5000/taxonomy');
            setTaxonomy(res.data);
        } catch (err) {
            console.error("Failed to fetch taxonomy", err);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newValue) return;
        try {
            await axios.post('http://localhost:5000/taxonomy?is_admin=true', {
                category,
                value: newValue
            });
            setMessage({ type: 'success', text: `Added ${newValue} to ${category}` });
            setNewValue('');
            fetchTaxonomy();
        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.error || 'Failed to add item' });
        }
    };

    const toggleStatus = async (item) => {
        const nextStatus = item.status === 'Active' ? 'Deprecated' : 'Active';
        try {
            await axios.patch(`http://localhost:5000/taxonomy/${item.id}?is_admin=true`, {
                status: nextStatus
            });
            fetchTaxonomy();
        } catch (err) {
            alert("Failed to update status");
        }
    };

    if (loading) return <div className="glass-panel" style={{ padding: '2rem' }}>Loading Governance Data...</div>;

    const docTypes = taxonomy.filter(t => t.category === 'DocumentType');
    const departments = taxonomy.filter(t => t.category === 'Department');

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="glass-panel" style={{ padding: '2rem' }}>
                <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Shield size={24} color="#60a5fa" /> Metadata Governance & Taxonomy
                </h2>

                <form onSubmit={handleAdd} style={{ display: 'flex', gap: '1rem', background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
                    <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Category</label>
                        <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
                            <option value="DocumentType">Document Type</option>
                            <option value="Department">Department</option>
                        </select>
                    </div>
                    <div style={{ flex: 2 }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>New Value</label>
                        <input
                            type="text"
                            className="input"
                            placeholder="e.g. Legal, Finance, Invoice..."
                            value={newValue}
                            onChange={e => setNewValue(e.target.value)}
                        />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button type="submit" className="btn" style={{ background: 'var(--primary)', borderColor: 'var(--primary)' }}>
                            <Plus size={18} /> Add Term
                        </button>
                    </div>
                </form>

                {message && (
                    <div style={{
                        marginBottom: '1.5rem',
                        padding: '1rem',
                        borderRadius: '8px',
                        background: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: message.type === 'success' ? '#4ade80' : '#f87171',
                        border: `1px solid ${message.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                    }}>
                        {message.status === 'success' ? <Check size={18} /> : <AlertCircle size={18} />} {message.text}
                    </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    {/* Document Types */}
                    <div>
                        <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>📄 Document Types</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {docTypes.map(item => (
                                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                                    <span style={{ textDecoration: item.status === 'Deprecated' ? 'line-through' : 'none', color: item.status === 'Deprecated' ? 'var(--text-muted)' : 'white' }}>
                                        {item.value}
                                    </span>
                                    <button
                                        onClick={() => toggleStatus(item)}
                                        className="btn btn-ghost"
                                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: item.status === 'Active' ? '#f87171' : '#4ade80' }}
                                    >
                                        <Power size={14} style={{ marginRight: '0.25rem' }} /> {item.status === 'Active' ? 'Deprecate' : 'Activate'}
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Departments */}
                    <div>
                        <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>🏢 Departments</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {departments.map(item => (
                                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                                    <span style={{ textDecoration: item.status === 'Deprecated' ? 'line-through' : 'none', color: item.status === 'Deprecated' ? 'var(--text-muted)' : 'white' }}>
                                        {item.value}
                                    </span>
                                    <button
                                        onClick={() => toggleStatus(item)}
                                        className="btn btn-ghost"
                                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: item.status === 'Active' ? '#f87171' : '#4ade80' }}
                                    >
                                        <Power size={14} style={{ marginRight: '0.25rem' }} /> {item.status === 'Active' ? 'Deprecate' : 'Activate'}
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="glass-panel" style={{ padding: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>🔐 Security & Governance Rules</h3>
                <ul style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>
                    <li>Sensitive documents (Confidential) are strictly hidden from search for general users.</li>
                    <li>Audit logs are persisted across schema changes; original metadata is preserved.</li>
                    <li>Field-level validation is active for <strong>Invoice</strong> (Due Date, Amount) and <strong>Contract</strong> schemas.</li>
                    <li>Deprecated taxonomy terms are hidden from the upload and intake forms.</li>
                </ul>
            </div>
        </div>
    );
};

export default GovernanceDashboard;
