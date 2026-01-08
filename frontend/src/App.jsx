import React, { useState, useEffect } from 'react';
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
import Login from './components/Login';
import { LayoutDashboard, Box, ScanLine, Microscope, BarChart3, Shield, User, UserCheck, Activity, Trash2, Briefcase, LogOut } from 'lucide-react';

function App() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [activeTab, setActiveTab] = useState('pipeline');
    const [globalSearch, setGlobalSearch] = useState('');

    // Auth State
    const [currentUser, setCurrentUser] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);

    useEffect(() => {
        // Check Session
        const storedUser = localStorage.getItem('kbn_user');
        if (storedUser) {
            const user = JSON.parse(storedUser);
            setCurrentUser(user);
            setIsAdmin(user.role === 'Admin' || user.role === 'Manager');
        }
    }, []);

    const handleLogin = (user) => {
        setCurrentUser(user);
        setIsAdmin(user.role === 'Admin' || user.role === 'Manager');
        localStorage.setItem('kbn_user', JSON.stringify(user));
        // Redirect logic (Show Default Tab)
        if (user.role === 'Operator' || user.role === 'Intern') {
            setActiveTab('intake');
        } else {
            setActiveTab('pipeline');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('kbn_user');
        setCurrentUser(null);
        setIsAdmin(false);
    };

    const handleUploadSuccess = () => {
        setRefreshKey(prev => prev + 1);
    };

    const handleGlobalSearch = (e) => {
        if (e.key === 'Enter') {
            setActiveTab('pipeline');
            setRefreshKey(prev => prev + 1);
        }
    };

    // 1. Login View
    if (!currentUser) {
        return <Login onLogin={handleLogin} />;
    }

    // Role-based Tab Visibility
    const isOps = currentUser.role === 'Operator' || currentUser.role === 'Intern';
    const canSeeAnalytics = isAdmin || currentUser.role === 'Manager';
    const canSeeGovernance = isAdmin;
    const canSeeCleanup = isAdmin;
    const canSeeAudit = isAdmin || currentUser.role === 'Manager';

    return (
        <div className="container">
            <header style={{
                marginBottom: '1rem',
                position: 'relative'
            }}>
                {/* Top Right Controls (Natural Flow - No Absolute Overlap) */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '1rem 2rem 0', // Top padding
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', padding: '0.4rem 0.8rem', borderRadius: '20px' }}>
                        <User size={16} />
                        <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{currentUser.name}</span>
                        <span style={{ fontSize: '0.8rem', opacity: 0.8, background: '#3b82f6', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>{currentUser.role}</span>
                    </div>

                    {isAdmin && (
                        <button
                            className="btn btn-ghost"
                            style={{ fontSize: '0.9rem', opacity: 0.9 }}
                            onClick={() => setActiveTab('access_requests')}
                        >
                            🔔 Requests
                        </button>
                    )}

                    <button
                        className="btn btn-ghost"
                        onClick={handleLogout}
                        title="Logout"
                        style={{ color: '#f87171' }}
                    >
                        <LogOut size={18} />
                    </button>
                </div>

                {/* Main Title Area (Centered below controls) */}
                <div style={{ textAlign: 'center', padding: '1rem 0 2rem' }}>
                    <h1 style={{ fontSize: '2.2rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>🚀 Document Sorting & Digitization System</h1>
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
                                style={{
                                    padding: '0.75rem 1rem 0.75rem 2.5rem',
                                    borderRadius: '25px',
                                    width: '450px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'white',
                                    fontSize: '1rem'
                                }}
                            />
                            <LayoutDashboard size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        </div>
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

                {(!isOps || true) && ( // Operators can see pipeline in my interpretation, just filtered
                    <button
                        onClick={() => setActiveTab('pipeline')}
                        className={`btn ${activeTab === 'pipeline' ? '' : 'btn-ghost'} `}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'pipeline' ? '#3b82f6' : 'transparent' }}
                    >
                        <ScanLine size={20} /> Digitization Pipeline
                    </button>
                )}

                <button
                    onClick={() => setActiveTab('qc')}
                    className={`btn ${activeTab === 'qc' ? '' : 'btn-ghost'} `}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'qc' ? '#3b82f6' : 'transparent' }}
                >
                    <Microscope size={20} /> QC Queue
                </button>

                {canSeeAnalytics && (
                    <>
                        <button
                            onClick={() => setActiveTab('workload')}
                            className={`btn ${activeTab === 'workload' ? '' : 'btn-ghost'} `}
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'workload' ? '#3b82f6' : 'transparent' }}
                        >
                            <Briefcase size={20} /> Workload
                        </button>
                        <button
                            onClick={() => setActiveTab('analytics')}
                            className={`btn ${activeTab === 'analytics' ? '' : 'btn-ghost'} `}
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'analytics' ? '#3b82f6' : 'transparent' }}
                        >
                            <BarChart3 size={20} /> Analytics
                        </button>
                    </>
                )}

                {canSeeGovernance && (
                    <button
                        onClick={() => setActiveTab('governance')}
                        className={`btn ${activeTab === 'governance' ? '' : 'btn-ghost'} `}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'governance' ? '#3b82f6' : 'transparent' }}
                    >
                        <Shield size={20} /> Governance
                    </button>
                )}

                {canSeeAudit && (
                    <button
                        onClick={() => setActiveTab('audit')}
                        className={`btn ${activeTab === 'audit' ? '' : 'btn-ghost'} `}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: activeTab === 'audit' ? '#3b82f6' : 'transparent' }}
                    >
                        <Activity size={20} /> Audit Center
                    </button>
                )}

                {canSeeCleanup && (
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
                        <IntakeForm onSuccess={() => setRefreshKey(prev => prev + 1)} currentUser={currentUser} />
                        <ContainerManager refreshTrigger={refreshKey} currentUser={currentUser} />
                    </div>
                ) : activeTab === 'qc' ? (
                    <QCQueue currentUser={currentUser} />
                ) : activeTab === 'workload' ? (
                    <WorkloadManager currentUser={currentUser} />
                ) : activeTab === 'analytics' ? (
                    <AnalyticsView currentUser={currentUser} />
                ) : activeTab === 'governance' ? (
                    <GovernanceDashboard currentUser={currentUser} />
                ) : activeTab === 'audit' ? (
                    <AuditCenter currentUser={currentUser} />
                ) : activeTab === 'cleanup' ? (
                    <CleanupReviews currentUser={currentUser} />
                ) : (
                    <>
                        {/* Only show upload pipeline if authorized? Prompt says Op/Intern see QC/Intake. 
                            But usually Operators DO upload. "Operator/Intern: See only 'Intake' or 'QC' status files" refers to VIEWS. 
                            I'll leave Upload enabled for now. 
                        */}
                        <DigitizationPipeline onUploadSuccess={handleUploadSuccess} currentUser={currentUser} />
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
