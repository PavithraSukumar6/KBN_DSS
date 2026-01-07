import React, { useState } from 'react';
import DigitizationPipeline from './components/DigitizationPipeline';
import Dashboard from './components/Dashboard';
import IntakeForm from './components/IntakeForm';
import ContainerManager from './components/ContainerManager';
import QCQueue from './components/QCQueue';
import AnalyticsView from './components/AnalyticsView';
import GovernanceDashboard from './components/GovernanceDashboard';

import AuditCenter from './components/AuditCenter';
import CleanupReviews from './components/CleanupReviews';
import WorkloadManager from './components/WorkloadManager';
import { LayoutDashboard, Box, ScanLine, Microscope, BarChart3, Shield, User, UserCheck, Activity, Trash2, Briefcase } from 'lucide-react';

function App() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [activeTab, setActiveTab] = useState('pipeline');
    const [globalSearch, setGlobalSearch] = useState('');

    // Auth Simulation
    const [users, setUsers] = useState([]);
    const [currentUser, setCurrentUser] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);

    React.useEffect(() => {
        // Fetch Users for simulation
        fetch('http://localhost:5000/users')
            .then(res => res.json())
            .then(data => {
                setUsers(data);
                // Default to Admin
                const admin = data.find(u => u.role === 'Admin');
                if (admin) {
                    setCurrentUser(admin);
                    setIsAdmin(true);
                }
            })
            .catch(err => console.error("Failed to load users", err));
    }, []);

    const handleUserSwitch = (userId) => {
        const user = users.find(u => u.id === userId);
        if (user) {
            setCurrentUser(user);
            setIsAdmin(user.role === 'Admin');
            setRefreshKey(prev => prev + 1); // Refresh all views
        }
    };

    const handleUploadSuccess = () => {
        setRefreshKey(prev => prev + 1);
    };

    const handleGlobalSearch = (e) => {
        if (e.key === 'Enter') {
            setActiveTab('pipeline'); // Go to library view
            setRefreshKey(prev => prev + 1);
        }
    };

    return (
        <div className="container">
            <header style={{
                textAlign: 'center',
                padding: '2rem 0',
                marginBottom: '1rem',
                position: 'relative'
            }}>
                <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', alignItems: 'center', gap: '1rem' }}>

                    {/* Access Request Dashboard Link (Admin Only) */}
                    {isAdmin && (
                        <button
                            className="btn btn-ghost"
                            style={{ fontSize: '0.8rem', opacity: 0.8 }}
                            onClick={() => setActiveTab('access_requests')}
                        >
                            🔔 Requests
                        </button>
                    )}
                </div>
                <h1>🚀 Document Sorting & Digitization System</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '1.5rem' }}>
                    Physical Intake • Digitization • Classification • Archival
                </p>
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <div style={{ position: 'relative' }}>
                        <input
                            type="text"
                            placeholder="Global Search Documents..."
                            value={globalSearch}
                            onChange={(e) => setGlobalSearch(e.target.value)}
                            onKeyDown={handleGlobalSearch}
                            style={{ padding: '0.65rem 1rem 0.65rem 2.5rem', borderRadius: '25px', width: '350px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white' }}
                        />
                        <LayoutDashboard size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                    </div>
                </div>
            </header>

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
                <button
                    onClick={() => setActiveTab('intake')}
                    className={`btn ${activeTab === 'intake' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'intake' ? '#3b82f6' : 'transparent' }}
                >
                    <Box size={20} /> Container Intake
                </button>
                <button
                    onClick={() => setActiveTab('pipeline')}
                    className={`btn ${activeTab === 'pipeline' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'pipeline' ? '#3b82f6' : 'transparent' }}
                >
                    <ScanLine size={20} /> Digitization Pipeline
                </button>
                <button
                    onClick={() => setActiveTab('qc')}
                    className={`btn ${activeTab === 'qc' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'qc' ? '#3b82f6' : 'transparent' }}
                >
                    <Microscope size={20} /> QC Queue
                </button>
                {isAdmin && (
                    <button
                        onClick={() => setActiveTab('workload')}
                        className={`btn ${activeTab === 'workload' ? '' : 'btn-ghost'} `}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'workload' ? '#3b82f6' : 'transparent' }}
                    >
                        <Briefcase size={20} /> Workload
                    </button>
                )}
                <button
                    onClick={() => setActiveTab('analytics')}
                    className={`btn ${activeTab === 'analytics' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'analytics' ? '#3b82f6' : 'transparent' }}
                >
                    <BarChart3 size={20} /> Analytics
                </button>
                <button
                    onClick={() => setActiveTab('governance')}
                    className={`btn ${activeTab === 'governance' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'governance' ? '#3b82f6' : 'transparent' }}
                >
                    <Shield size={20} /> Governance
                </button>
                <button
                    onClick={() => setActiveTab('audit')}
                    className={`btn ${activeTab === 'audit' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'audit' ? '#3b82f6' : 'transparent' }}
                >
                    <Activity size={20} /> Audit Center
                </button>
                {isAdmin && (
                    <button
                        onClick={() => setActiveTab('cleanup')}
                        className={`btn ${activeTab === 'cleanup' ? '' : 'btn-ghost'} `}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'cleanup' ? '#3b82f6' : 'transparent', color: '#f87171' }}
                    >
                        <Trash2 size={20} /> Cleanup
                    </button>
                )}
            </div>

            <main>
                {activeTab === 'intake' ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 1fr) 1fr', gap: '2rem' }}>
                        <IntakeForm onSuccess={() => setRefreshKey(prev => prev + 1)} />
                        <ContainerManager refreshTrigger={refreshKey} />
                    </div>
                ) : activeTab === 'qc' ? (
                    <QCQueue />
                ) : activeTab === 'workload' ? (
                    <WorkloadManager />
                ) : activeTab === 'analytics' ? (
                    <AnalyticsView />
                ) : activeTab === 'governance' ? (
                    <GovernanceDashboard />
                ) : activeTab === 'audit' ? (
                    <AuditCenter currentUser={currentUser} />
                ) : activeTab === 'cleanup' ? (
                    <CleanupReviews currentUser={currentUser} />
                ) : (
                    <>
                        <DigitizationPipeline onUploadSuccess={handleUploadSuccess} />
                        <Dashboard refreshTrigger={refreshKey} globalSearch={globalSearch} isAdmin={isAdmin} currentUser={currentUser} />
                    </>
                )}
            </main>

            <footer style={{
                textAlign: 'center',
                padding: '2rem',
                color: 'var(--text-muted)',
                marginTop: '3rem',
                borderTop: '1px solid var(--glass-border)'
            }}>
                <p>Built with Flask + React • 2024</p>
            </footer>
        </div>
    );
}

export default App;
