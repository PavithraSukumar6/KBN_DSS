import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Save, User, MapPin, Scan, FolderTree as TreeIcon } from 'lucide-react';

const IntakeForm = ({ onSuccess }) => {
    const [formData, setFormData] = useState({
        id: '',
        name: '',
        subsidiary: 'Headquarters',
        department: '',
        function: '',
        date_range: '',
        confidentiality_level: 'General',
        source_location: 'Reception',
        created_by: '',
        physical_page_count: '',
        parent_id: 'ROOT'
    });

    const [loading, setLoading] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [message, setMessage] = useState(null);

    const [taxonomy, setTaxonomy] = useState([]);
    const [containers, setContainers] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [taxRes, contRes] = await Promise.all([
                    axios.get('http://localhost:5000/taxonomy?category=Department'),
                    axios.get('http://localhost:5000/containers')
                ]);
                setTaxonomy(taxRes.data.filter(t => t.status === 'Active'));
                setContainers(contRes.data);
            } catch (err) { console.error(err); }
        };
        fetchData();
    }, []);

    const generateId = () => {
        const id = 'BOX-' + Math.random().toString(36).substr(2, 9).toUpperCase();
        setFormData(prev => ({ ...prev, id, name: prev.name || id }));
    };

    const handleDirectScan = async () => {
        setScanning(true);
        setMessage(null);
        try {
            const res = await axios.post('http://localhost:5000/scan/direct');
            setMessage({ type: 'success', text: `Direct Scan Successful: ${res.data.filename}` });
            // Optionally auto-set form data from scan? For now just notify.
        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.error || 'Direct Scan failed. Ensure scanner is connected.' });
        } finally {
            setScanning(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        try {
            await axios.post('http://localhost:5000/containers', formData);
            setMessage({ type: 'success', text: `Container ${formData.name || formData.id} Created Successfully!` });
            if (onSuccess) onSuccess();
            // Reset form but keep some defaults
            setFormData(prev => ({
                ...prev,
                id: '',
                name: '',
                department: '',
                function: '',
                date_range: '',
                physical_page_count: ''
            }));
        } catch (error) {
            setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to create container' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                    <Box size={24} /> New Container Intake
                </h2>
                <button
                    type="button"
                    onClick={handleDirectScan}
                    disabled={scanning}
                    className="btn btn-ghost"
                    style={{ border: '1px solid #3b82f6', color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                >
                    <Scan size={18} /> {scanning ? "Scanning..." : "Direct Scan"}
                </button>
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

                {/* Parent Folder selection */}
                <div>
                    <label className="label">Parent Folder (Location in Hierarchy)</label>
                    <div style={{ position: 'relative' }}>
                        <TreeIcon size={16} style={{ position: 'absolute', left: '10px', top: '12px', color: '#9ca3af' }} />
                        <select
                            name="parent_id"
                            value={formData.parent_id}
                            onChange={handleChange}
                            className="input"
                            style={{ paddingLeft: '2.5rem' }}
                        >
                            {containers.map(c => (
                                <option key={c.id} value={c.id}>{c.name || c.id}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* ID & Name Section */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '1rem' }}>
                    <div>
                        <label className="label">Container ID (Barcode)</label>
                        <input
                            type="text"
                            name="id"
                            value={formData.id}
                            onChange={handleChange}
                            placeholder="Optional"
                            style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
                        />
                    </div>
                    <div>
                        <label className="label">Container Name</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="Display Name"
                            required
                            style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
                        />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button type="button" onClick={generateId} className="btn" style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
                            Auto-ID
                        </button>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label className="label">Subsidiary</label>
                        <select name="subsidiary" value={formData.subsidiary} onChange={handleChange} className="input">
                            <option>Headquarters</option>
                            <option>Branch NY</option>
                            <option>Branch LA</option>
                        </select>
                    </div>
                    <div>
                        <label className="label">Department</label>
                        <select name="department" value={formData.department} onChange={handleChange} className="input" required>
                            <option value="">-- Select Department --</option>
                            {taxonomy.map(t => <option key={t.id} value={t.value}>{t.value}</option>)}
                        </select>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label className="label">Confidentiality</label>
                        <select name="confidentiality_level" value={formData.confidentiality_level} onChange={handleChange} className="input">
                            <option>Public</option>
                            <option>Internal</option>
                            <option>Confidential</option>
                            <option>Restricted</option>
                        </select>
                    </div>
                    <div>
                        <label className="label">Date Range (Est)</label>
                        <input type="text" name="date_range" value={formData.date_range} onChange={handleChange} className="input" placeholder="e.g. 2020-2023" />
                    </div>
                    <div>
                        <label className="label">Physical Page Count</label>
                        <input type="number" name="physical_page_count" value={formData.physical_page_count} onChange={handleChange} className="input" placeholder="Total Pages" min="0" />
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '1rem' }}>
                    <div>
                        <label className="label">Source Location</label>
                        <div style={{ position: 'relative' }}>
                            <MapPin size={16} style={{ position: 'absolute', left: '10px', top: '12px', color: '#9ca3af' }} />
                            <input type="text" name="source_location" value={formData.source_location} onChange={handleChange} className="input" style={{ paddingLeft: '2rem' }} required />
                        </div>
                    </div>
                    <div>
                        <label className="label">Operator ID</label>
                        <div style={{ position: 'relative' }}>
                            <User size={16} style={{ position: 'absolute', left: '10px', top: '12px', color: '#9ca3af' }} />
                            <input type="text" name="created_by" value={formData.created_by} onChange={handleChange} className="input" style={{ paddingLeft: '2rem' }} placeholder="Your ID" required />
                        </div>
                    </div>
                </div>

                <button type="submit" className="btn" disabled={loading} style={{ marginTop: '1rem', background: '#3b82f6' }}>
                    {loading ? 'Registering...' : <><Save size={18} /> Register Container</>}
                </button>
            </form>

            {message && (
                <div style={{
                    marginTop: '1rem',
                    padding: '1rem',
                    borderRadius: '8px',
                    background: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: message.type === 'success' ? '#4ade80' : '#f87171',
                    border: `1px solid ${message.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                }}>
                    {message.text}
                </div>
            )}

            <style>{`
                .label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; color: var(--text-muted); }
                .input { width: 100%; padding: 0.75rem; border-radius: 6px; border: 1px solid var(--glass-border); background: rgba(0,0,0,0.2); color: white; }
            `}</style>
        </div>
    );
};

export default IntakeForm;
