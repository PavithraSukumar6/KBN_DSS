
import React, { useState } from 'react';
import axios from 'axios';
import { User, Lock, Shield, ArrowRight, ScanLine } from 'lucide-react';

const Login = ({ onLogin }) => {
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('Admin');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const res = await axios.post('http://localhost:5000/login', {
                user_id: userId,
                password: password,
                role: role
            });

            // Success
            onLogin(res.data.user);
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            height: '100vh', width: '100vw',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            color: 'white'
        }}>
            <div className="glass-panel" style={{
                padding: '3rem', width: '400px', borderRadius: '16px',
                border: '1px solid rgba(255,255,255,0.1)'
            }}>
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        width: '64px', height: '64px', background: 'rgba(96, 165, 250, 0.2)',
                        borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        margin: '0 auto 1rem'
                    }}>
                        <ScanLine size={32} color="#60a5fa" />
                    </div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>KBN Digitization</h1>
                    <p style={{ color: '#94a3b8' }}>Secure Access Portal</p>
                </div>

                <form onSubmit={handleLogin}>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>Role</label>
                        <div style={{ position: 'relative' }}>
                            <Shield size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b', pointerEvents: 'none' }} />
                            <select
                                value={role} onChange={e => setRole(e.target.value)}
                                className="input"
                                style={{ width: '100%', paddingLeft: '40px', appearance: 'none' }}
                            >
                                <option value="Admin">Admin</option>
                                <option value="Manager">Manager</option>
                                <option value="Operator">Operator</option>
                                <option value="Viewer">Viewer</option>
                                <option value="Intern">Intern</option>
                            </select>
                        </div>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>User ID</label>
                        <div style={{ position: 'relative' }}>
                            <User size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b', pointerEvents: 'none' }} />
                            <input
                                type="text"
                                value={userId} onChange={e => setUserId(e.target.value)}
                                placeholder="e.g. Gokul_Admin"
                                className="input"
                                style={{ width: '100%', paddingLeft: '40px' }}
                                required
                            />
                        </div>
                    </div>

                    <div style={{ marginBottom: '2rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>Password</label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b', pointerEvents: 'none' }} />
                            <input
                                type="password"
                                value={password} onChange={e => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="input"
                                style={{ width: '100%', paddingLeft: '40px' }}
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div style={{
                            padding: '0.75rem', marginBottom: '1.5rem',
                            background: 'rgba(239, 68, 68, 0.1)', color: '#f87171',
                            borderRadius: '8px', fontSize: '0.9rem', textAlign: 'center'
                        }}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn"
                        style={{ width: '100%', justifyContent: 'center', background: '#3b82f6', height: '44px' }}
                    >
                        {loading ? 'Authenticating...' : (
                            <>Sign In <ArrowRight size={18} style={{ marginLeft: '8px' }} /></>
                        )}
                    </button>

                    <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.8rem', color: '#64748b' }}>
                        Demo Credentials: admin123, manager123...
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Login;
