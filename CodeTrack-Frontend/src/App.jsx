
import React, { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowUpRight, BarChart3, Bell, BookOpen, Check, CheckCircle2, ChevronDown, Code2, Filter, Flame, LayoutDashboard, ListChecks, Menu, Plus, RefreshCw, Search, Settings, ShieldCheck, Sparkles, Target, Trophy, Trash2, X, CalendarDays, Clock3, ExternalLink, CircleDashed } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, BarChart as RBarChart, Bar } from 'recharts';

const starter=[
{id:1,title:'Two Sum',platform:'LeetCode',topic:'Arrays & Hashing',difficulty:'Easy',status:'Solved',date:'2026-10-21',url:'https://leetcode.com/problems/two-sum/',notes:'Use a map to store the value and its index.'},
{id:2,title:'Longest Substring Without Repeating Characters',platform:'LeetCode',topic:'Sliding Window',difficulty:'Medium',status:'Revision',date:'2026-10-20',url:'https://leetcode.com/problems/longest-substring-without-repeating-characters/',notes:'Revise the window boundaries and last-seen index.'},
{id:3,title:'Valid Parentheses',platform:'LeetCode',topic:'Stack',difficulty:'Easy',status:'Solved',date:'2026-10-19',url:'https://leetcode.com/problems/valid-parentheses/',notes:'Stack works well for matching pairs.'},
{id:4,title:'Merge Two Sorted Lists',platform:'LeetCode',topic:'Linked List',difficulty:'Easy',status:'Attempted',date:'2026-10-18',url:'https://leetcode.com/problems/merge-two-sorted-lists/',notes:''},
{id:5,title:'Product of Array Except Self',platform:'LeetCode',topic:'Arrays & Hashing',difficulty:'Medium',status:'Solved',date:'2026-10-17',url:'https://leetcode.com/problems/product-of-array-except-self/',notes:'Prefix and suffix products; no division.'},
{id:6,title:'Binary Tree Level Order Traversal',platform:'LeetCode',topic:'Trees',difficulty:'Medium',status:'Revision',date:'2026-10-16',url:'https://leetcode.com/problems/binary-tree-level-order-traversal/',notes:'Use a queue for BFS level traversal.'}];


const blank=()=>({title:'',platform:'LeetCode',topic:'Arrays & Hashing',difficulty:'Medium',status:'Solved',date:new Date().toISOString().slice(0,10),url:'',notes:''});
function Stat({label,value,sub,icon:Icon,tone}){return <div className="stat"><div className={'stat-icon '+tone}><Icon size={18}/></div><div><span>{label}</span><strong>{value}</strong><small>{sub}</small></div></div>}
function Modal({title,onClose,children}){return <div className="backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><section className="modal"><div className="modal-head"><h2>{title}</h2><button className="icon" onClick={onClose}><X size={18}/></button></div>{children}</section></div>}
export default function App(){
const[page,setPage]=useState('Overview'),[workspaceOpen,setWorkspaceOpen]=useState(false),[profileOpen,setProfileOpen]=useState(false),[compactMode,setCompactMode]=useState(false),[showNotifications,setShowNotifications]=useState(true),[problems,setProblems]=useState([]),[query,setQuery]=useState(''),[status,setStatus]=useState('All statuses'),[difficulty,setDifficulty]=useState('All difficulties'),[modal,setModal]=useState(false),[edit,setEdit]=useState(null),[form,setForm]=useState(blank()),[mobile,setMobile]=useState(false),[toast,setToast]=useState('');
const [loading, setLoading] = useState(true);
const [loadError, setLoadError] = useState('');
const [saving, setSaving] = useState(false);
const [token, setToken] = useState(() => localStorage.getItem('codetrack_token') || '');
const [currentUser, setCurrentUser] = useState(null);
const [authMode, setAuthMode] = useState('login');
const [authName, setAuthName] = useState('');
const [authEmail, setAuthEmail] = useState('');
const [authPassword, setAuthPassword] = useState('');
const [authBusy, setAuthBusy] = useState(false);
const [authError, setAuthError] = useState('');
const notify = (t) => {
  if (!showNotifications) return;
  setToast(t);
  setTimeout(() => setToast(''), 2400);
};

const solved = problems.filter(p => p.status === 'Solved').length;
const revision = problems.filter(p => p.status === 'Revision').length;
const attempted = problems.filter(p => p.status === 'Attempted').length;

const weeklyGoal = 25;

const weekStart = new Date();
weekStart.setHours(0, 0, 0, 0);
weekStart.setDate(weekStart.getDate() - 6);

const weeklySolved = problems.filter(p => {
  if (p.status !== 'Solved' || !p.date) return false;

  const problemDate = new Date(`${p.date}T00:00:00`);
  return problemDate >= weekStart && problemDate <= new Date();
}).length;

const weeklyProgress = Math.min(
  100,
  Math.round((weeklySolved / weeklyGoal) * 100)
);
const API = 'http://localhost:8081/api/v1/problems';
const AUTH_API = 'http://localhost:8081/api/v1/auth';
const authHeaders = (extra = {}) => ({ ...extra, Authorization: `Bearer ${token}` });

const logout = () => {
  localStorage.removeItem('codetrack_token');
  setToken('');
  setCurrentUser(null);
  setProblems([]);
  setPage('Overview');
};

const handleAuth = async (e) => {
  e.preventDefault();
  setAuthBusy(true);
  setAuthError('');
  try {
    const isRegister = authMode === 'register';
    const response = await fetch(`${AUTH_API}/${isRegister ? 'register' : 'login'}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(isRegister
        ? { name: authName.trim(), email: authEmail.trim(), password: authPassword }
        : { email: authEmail.trim(), password: authPassword })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || data.error || (isRegister ? 'Registration failed.' : 'Invalid email or password.'));
    if (isRegister) {
      setAuthMode('login');
      setAuthPassword('');
      setAuthError('Account created. Please log in.');
      return;
    }
    localStorage.setItem('codetrack_token', data.token);
    setToken(data.token);
    setCurrentUser({ id: data.id, name: data.name, email: data.email });
    setAuthPassword('');
  } catch (err) {
    setAuthError(err.message || 'Could not connect to the backend.');
  } finally {
    setAuthBusy(false);
  }
};

useEffect(() => {
  if (!token) {
    setCurrentUser(null);
    setProblems([]);
    setLoading(false);
    return;
  }
  let cancelled = false;
  const loadAccount = async () => {
    setLoading(true);
    setLoadError('');
    try {
      const [meResponse, problemsResponse] = await Promise.all([
        fetch(`${AUTH_API}/me`, { headers: authHeaders() }),
        fetch(API, { headers: authHeaders() })
      ]);
      if (meResponse.status === 401 || meResponse.status === 403 || problemsResponse.status === 401 || problemsResponse.status === 403) {
        logout();
        return;
      }
      if (!meResponse.ok) throw new Error('Could not load your account.');
      if (!problemsResponse.ok) throw new Error(`Could not load problems (HTTP ${problemsResponse.status}).`);
      const me = await meResponse.json();
      const data = await problemsResponse.json();
      if (!cancelled) {
        setCurrentUser(me);
        setProblems(data.map(toFrontend));
      }
    } catch (err) {
      if (!cancelled) setLoadError(err.message || 'Could not load your account and problems.');
    } finally {
      if (!cancelled) setLoading(false);
    }
  };
  loadAccount();
  return () => { cancelled = true; };
}, [token]);

const toFrontend = (p) => ({
  ...p,
  date: p.solvedDate ?? '',
  status: ({
    SOLVED: 'Solved',
    IN_PROGRESS: 'Attempted',
    TODO: 'Revision'
  })[p.status] ?? 'Revision'
});

const toBackend = (p) => ({
  title: p.title,
  platform: p.platform,
  topic: p.topic,
  url:p.url,
  difficulty: p.difficulty,
  solvedDate: p.date || null,
  notes: p.notes,
  status: ({
    Solved: 'SOLVED',
    Attempted: 'IN_PROGRESS',
    Revision: 'TODO'
  })[p.status] ?? 'TODO'
});

const week = useMemo(() => {
  const today = new Date();
  const start = new Date(today);
  start.setDate(today.getDate() - 6);
  start.setHours(0, 0, 0, 0);

  const days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(start);
    date.setDate(start.getDate() + i);

    return {
      date: date.toISOString().slice(0, 10),
      day: date.toLocaleDateString('en-US', {
        weekday: 'short'
      }),
      solved: 0
    };
  });

  problems.forEach((problem) => {
    if (problem.status !== 'Solved' || !problem.date) return;

    const day = days.find((item) => item.date === problem.date);
    if (day) day.solved++;
  });

  return days;
}, [problems]);

const topics = useMemo(() => {
  const counts = {};

  problems.forEach((problem) => {
    const topic = problem.topic?.trim() || 'Uncategorized';
    counts[topic] = (counts[topic] || 0) + 1;
  });

  return Object.entries(counts)
    .map(([topic, count]) => ({ topic, count }))
    .sort((a, b) => b.count - a.count);
}, [problems]);

const filtered=useMemo(()=>problems.filter(p=>(p.title+' '+p.topic+' '+p.platform).toLowerCase().includes(query.toLowerCase())&&(status==='All statuses'||p.status===status)&&(difficulty==='All difficulties'||p.difficulty===difficulty)),[problems,query,status,difficulty]);

const add = () => {
  setEdit(null);
  setForm(blank());
  setModal(true);
};

const editProblem = (p) => {
  setEdit(p.id);
  setForm({ ...p });
  setModal(true);
};

const submit = async (e) => {
  e.preventDefault();

  if (saving) return;

  if (!form.title.trim()) {
    notify('Problem title is required');
    return;
  }

  if (form.url.trim()) {
    try {
      const parsedUrl = new URL(form.url);

      if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
        notify('Problem URL must start with http:// or https://');
        return;
      }
    } catch {
      notify('Please enter a valid problem URL');
      return;
    }
  }

  setSaving(true);

  try {
    const response = await fetch(
      edit ? `${API}/${edit}` : API,
      {
        method: edit ? 'PUT' : 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(toBackend(form))
      }
    );

    if (!response.ok) {
      throw new Error(await response.text());
    }

    const savedProblem = toFrontend(await response.json());

    setProblems((current) =>
      edit
        ? current.map((p) => p.id === edit ? savedProblem : p)
        : [savedProblem, ...current]
    );

    setModal(false);
    notify(edit ? 'Problem updated in MySQL' : 'Problem saved to MySQL');
  } catch (error) {
    console.error('Saving failed:', error);
    notify('Could not save. Check the browser console.');
  } finally {
    setSaving(false);
  }
};

const remove = async (id) => {
  if (!confirm('Delete this problem?')) return;

  try {
    const response = await fetch(`${API}/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });

    if (!response.ok) throw new Error('Delete failed');

    setProblems((current) => current.filter((p) => p.id !== id));
    notify('Problem deleted from MySQL');
  } catch (error) {
    console.error('Delete failed:', error);
    notify('Could not delete the problem');
  }
};

const setProblemStatus = async (id, newStatus) => {
  const problem = problems.find((p) => p.id === id);
  if (!problem) return;

  try {
    const response = await fetch(`${API}/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(toBackend({ ...problem, status: newStatus }))
    });

    if (!response.ok) throw new Error(await response.text());

    const updated = toFrontend(await response.json());

    setProblems((current) =>
      current.map((p) => p.id === id ? updated : p)
    );

    notify('Status saved to MySQL');
  } catch (error) {
    console.error('Status update failed:', error);
    notify('Could not update status');
  }
};

const nav=[['Overview',LayoutDashboard],['Problem Tracker',ListChecks],['Revision Notes',BookOpen],['Analytics',BarChart3],['Weekly goals',Target]];
const authInputStyle = { width:'100%',boxSizing:'border-box',padding:'11px 12px',border:'1px solid #dfe2ed',borderRadius:9,fontSize:14,outlineColor:'#7667f5' };

if (!token) {
  return <div style={{minHeight:'100vh',display:'grid',placeItems:'center',padding:24,background:'#f6f7fb',fontFamily:'inherit'}}>
    <section style={{width:'100%',maxWidth:420,background:'#fff',padding:32,borderRadius:20,boxShadow:'0 18px 55px #20204012',border:'1px solid #e9eaf2'}}>
      <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:24}}><div style={{width:44,height:44,display:'grid',placeItems:'center',background:'#7667f5',color:'#fff',borderRadius:13}}><Code2 size={23}/></div><div><h1 style={{fontSize:23,margin:0,color:'#20213a'}}>CodeTrack</h1><p style={{margin:'4px 0 0',fontSize:12,color:'#9299ad'}}>YOUR PERSONAL DSA WORKSPACE</p></div></div>
      <h2 style={{margin:'0 0 8px',fontSize:22,color:'#20213a'}}>{authMode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
      <p style={{margin:'0 0 22px',color:'#777f96',fontSize:14}}>{authMode === 'login' ? 'Log in to continue tracking your progress.' : 'Create an account to keep your problems private.'}</p>
      <form onSubmit={handleAuth} style={{display:'grid',gap:14}}>
        {authMode === 'register' && <label style={{display:'grid',gap:6,fontSize:13,color:'#555d74'}}>Name<input required maxLength={100} value={authName} onChange={e=>setAuthName(e.target.value)} autoComplete="name" style={authInputStyle}/></label>}
        <label style={{display:'grid',gap:6,fontSize:13,color:'#555d74'}}>Email<input required type="email" value={authEmail} onChange={e=>setAuthEmail(e.target.value)} autoComplete="email" style={authInputStyle}/></label>
        <label style={{display:'grid',gap:6,fontSize:13,color:'#555d74'}}>Password<input required minLength={8} type="password" value={authPassword} onChange={e=>setAuthPassword(e.target.value)} autoComplete={authMode === 'login' ? 'current-password' : 'new-password'} style={authInputStyle}/></label>
        {authError && <p role="alert" style={{margin:0,fontSize:13,color:authError.includes('created')?'#16845b':'#c43e52'}}>{authError}</p>}
        <button type="submit" disabled={authBusy} style={{marginTop:4,padding:'12px 16px',border:0,borderRadius:10,background:'#7667f5',color:'#fff',fontWeight:700,cursor:authBusy?'wait':'pointer'}}>{authBusy ? 'Please wait…' : authMode === 'login' ? 'Log in' : 'Create account'}</button>
      </form>
      <p style={{textAlign:'center',fontSize:13,color:'#777f96',margin:'20px 0 0'}}>{authMode === 'login' ? "Don't have an account? " : 'Already registered? '}<button onClick={()=>{setAuthMode(authMode === 'login' ? 'register' : 'login');setAuthError('')}} style={{border:0,background:'none',color:'#6655ed',fontWeight:700,cursor:'pointer'}}>{authMode === 'login' ? 'Register' : 'Log in'}</button></p>
    </section>
  </div>;
}

return <div className="shell"><aside className={'sidebar '+(mobile?'open':'')}><div className="brand"><div className="brand-icon"><Code2/></div><div><b>CodeTrack</b><small>DSA WORKSPACE</small></div><button className="mobile-close icon" onClick={()=>setMobile(false)}><X/></button></div><div style={{position:'relative',margin:'0 10px 20px'}}><button type="button" className="workspace" style={{width:'100%',textAlign:'left',cursor:'pointer',font:'inherit',color:'inherit',background:workspaceOpen?'#f7f6ff':'',border:workspaceOpen?'1px solid #d9d4ff':''}} onClick={()=>setWorkspaceOpen(v=>!v)} aria-expanded={workspaceOpen}><div className="workspace-mark">CT</div><div style={{flex:1}}><b>Personal workspace</b><small>Personal Workspace</small></div><ChevronDown size={15} style={{transform:workspaceOpen?'rotate(180deg)':'none',transition:'transform .15s'}}/></button>{workspaceOpen&&<div style={{position:'absolute',zIndex:30,top:'calc(100% + 6px)',left:0,right:0,background:'#fff',border:'1px solid #e5e7ef',borderRadius:12,padding:8,boxShadow:'0 12px 30px #2020401a'}}><div style={{padding:'9px 10px',fontSize:12,color:'#9299ad'}}>CURRENT WORKSPACE</div><button className="nav-item active" style={{width:'100%'}} onClick={()=>{setWorkspaceOpen(false);setPage('Overview')}}><Code2 size={17}/><span>Personal workspace</span><Check size={15}/></button><button className="nav-item" style={{width:'100%'}} onClick={()=>{setWorkspaceOpen(false);notify('This is the local demo workspace. Multi-workspace support can be added later.')}}><Plus size={17}/><span>Create workspace</span></button><button className="nav-item" style={{width:'100%'}} onClick={()=>{setWorkspaceOpen(false);setPage('Settings')}}><Settings size={17}/><span>Workspace settings</span></button></div>}</div><label className="nav-label">WORKSPACE</label>{nav.slice(0,4).map(([n,I])=><button key={n} className={'nav-item '+(page===n?'active':'')} onClick={()=>{setPage(n);setMobile(false)}}><I size={18}/><span>{n}</span>{n==='Revision Notes'&&revision>0&&<em>{revision}</em>}</button>)}<label className="nav-label personal">PERSONAL</label><button className={'nav-item '+(page==='Weekly goals'?'active':'')} onClick={()=>setPage('Weekly goals')}><Target size={18}/><span>Weekly goals</span></button><button className={'nav-item '+(page==='Settings'?'active':'')} onClick={()=>{setPage('Settings');setMobile(false)}}><Settings size={18}/><span>Settings</span></button><div className="push"/><div className="goal-card"><div className="goal-head"><span><Flame size={14}/> Weekly target</span><b>{weeklyProgress}%</b></div><div className="progress">
  <i style={{ width: `${weeklyProgress}%` }} />
</div><p>{weeklySolved} of {weeklyGoal} problems completed</p><small>You're building a solid habit.</small></div><button type="button" className="user" style={{width:'100%',textAlign:'left',cursor:'pointer',font:'inherit',color:'inherit',background:profileOpen?'#f7f6ff':''}} onClick={()=>setProfileOpen(true)}><div className="avatar">{(currentUser?.name || 'U').charAt(0).toUpperCase()}</div><div style={{flex:1}}><b>{currentUser?.name || 'Your profile'}</b><small>{currentUser?.email || 'CodeTrack Profile'}</small></div><ChevronDown size={14}/></button></aside>{mobile&&<div className="scrim" onClick={()=>setMobile(false)}/>}<main className="main"><header className="topbar"><div className="crumb"><button className="mobile-menu icon" onClick={()=>setMobile(true)}><Menu/></button>Workspace <span>/</span> <b>{page}</b></div><div className="top-right"><div className="date-chip"><CalendarDays size={15}/>{new Date().toLocaleDateString('en-US', {
  weekday: 'long',
  month: 'short',
  day: 'numeric'
})}</div><button className="icon" onClick={()=>notify(`${revision} problem(s) marked for revision`)}><Bell size={18}/></button><div className="avatar top-avatar">{(currentUser?.name || 'U').charAt(0).toUpperCase()}</div></div></header><div className="content">

{loading && (
  <div className="empty">Loading your problems...</div>
)}

{!loading && loadError && (
  <div className="empty">
    <p>{loadError}</p>
    <button
      className="primary"
      onClick={() => window.location.reload()}
    >
      Try again
    </button>
  </div>
)}

{!loading && !loadError && (
  <>
{page==='Overview'&&<><div className="welcome"><div><div className="eyebrow"><Sparkles size={14}/> YOUR LEARNING, IN FOCUS</div><h1>Good morning, coder <span>✦</span></h1><p>Small steps. Consistent practice. Real progress.</p></div><button className="primary" onClick={add}><Plus size={17}/> Add a problem</button></div><section className="hero"><div className="hero-copy"><div className="hero-tag"><Activity size={14}/> YOUR WEEK AT A GLANCE</div><h2>You're showing up.<br/><span>That's what counts.</span></h2><p>Every problem you solve makes the next one a little easier. Keep your streak alive and trust the process.</p><button className="hero-button" onClick={()=>setPage('Problem Tracker')}>View your tracker <ExternalLink size={14}/></button></div><div className="hero-art"><div className="orbit one"/><div className="orbit two"/><div className="code-card"><div className="dots"><i/><i/><i/></div><b/><b/><b/><b/><b/></div><div className="float-score"><Trophy size={17}/><div><b>{solved} problems solved</b>
<small>Keep building your progress!</small></div></div><div className="float-check"><Check/></div></div></section><div className="stats"><Stat label="Problems solved" value={solved} sub="Across all topics" icon={CheckCircle2} tone="green"/><Stat label="Need revision" value={revision} sub="Keep concepts fresh" icon={RefreshCw} tone="purple"/><Stat label="Attempted" value={attempted} sub="Ready for another try" icon={CircleDashed} tone="orange"/><Stat label="Total tracked" value={problems.length} sub="Your coding journey" icon={Code2} tone="blue"/></div><div className="grid"><section className="panel"><div className="panel-head"><div><h3>Weekly activity</h3><p>Your practice, day by day</p></div><span className="pill-select">This week <ChevronDown size={13}/></span></div><div className="legend"><i/> Problems solved <small>Last 7 days</small></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={week} margin={{top:10,right:5,left:-22,bottom:0}}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7667f5" stopOpacity={.24}/><stop offset="100%" stopColor="#7667f5" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#edf0f6" vertical={false}/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill:'#9299ad',fontSize:11}} dy={9}/><YAxis axisLine={false} tickLine={false} tick={{fill:'#9299ad',fontSize:11}}/><Tooltip/><Area type="monotone" dataKey="solved" stroke="#7667f5" strokeWidth={2.5} fill="url(#fill)"/></AreaChart></ResponsiveContainer></div></section><section className="panel"><div className="panel-head"><div><h3>Topics in motion</h3><p>Where you've been practicing</p></div><button className="icon" onClick={()=>setPage('Analytics')}><ArrowUpRight/></button></div><div className="topic-list">{topics.map((t,i)=><div key={t.topic}><div className="topic-meta"><span>{t.topic}</span><b>{t.count}</b></div><div className="track"><i className={'color-'+i} style={{width:((t.count / Math.max(...topics.map(t => t.count), 1)) * 100)+'%'}}/></div></div>)}</div><button className="link" onClick={()=>setPage('Analytics')}>View topic analytics <ArrowUpRight size={14}/></button></section></div><section className="panel recent"><div className="panel-head"><div><h3>Recently tracked</h3><p>Your latest problem activity</p></div><button className="link" onClick={()=>setPage('Problem Tracker')}>View all <ArrowUpRight size={14}/></button></div><ProblemTable problems={problems.slice(0,4)} onEdit={editProblem} onDelete={remove} onStatus={setProblemStatus}/></section><div className="foot"><ShieldCheck size={15}/>Your progress is synced with the CodeTrack backend.</div></>}
{page==='Problem Tracker'&&<><div className="page-title"><div><div className="eyebrow">YOUR PRACTICE LIBRARY</div><h1>Problem tracker</h1><p>Keep every attempt, insight, and revision in one place.</p></div><button className="primary" onClick={add}><Plus size={17}/> Add a problem</button></div><section className="panel tracker"><div className="toolbar"><div className="search"><Search size={16}/><input placeholder="Search problems, topics, platforms..." value={query} onChange={e=>setQuery(e.target.value)}/></div><div className="filters"><div className="filter"><Filter size={14}/><select value={status} onChange={e=>setStatus(e.target.value)}><option>All statuses</option><option>Solved</option><option>Attempted</option><option>Revision</option></select></div><select className="select" value={difficulty} onChange={e=>setDifficulty(e.target.value)}><option>All difficulties</option><option>Easy</option><option>Medium</option><option>Hard</option></select></div></div><ProblemTable problems={filtered} onEdit={editProblem} onDelete={remove} onStatus={setProblemStatus} empty="No matching problems. Change the filters or add a problem."/></section></>}
{page==='Revision Notes'&&<><div className="page-title"><div><div className="eyebrow">REMEMBER WHAT YOU LEARN</div><h1>Revision notes</h1><p>Short reminders for concepts you want to revisit.</p></div><button className="primary" onClick={()=>{setStatus('Revision');setPage('Problem Tracker')}}><BookOpen size={16}/> See revision queue</button></div><div className="notes-grid">{problems.filter(p=>p.notes?.trim()).map(p=><article className="note" key={p.id}><div className="note-top"><span className={'difficulty '+p.difficulty.toLowerCase()}>{p.difficulty}</span><button className="icon" onClick={()=>editProblem(p)}><ExternalLink size={15}/></button></div><h3>{p.title}</h3><small>{p.topic} · {p.platform}</small><p>{p.notes}</p><div className="note-bottom"><span><Clock3 size={13}/> {p.date}</span><button onClick={()=>setProblemStatus(p.id,p.status==='Revision'?'Solved':'Revision')}>{p.status==='Revision'?'Mark revised':'Add to revision'} <ArrowUpRight size={13}/></button></div></article>)}</div>{!problems.some(p=>p.notes?.trim())&&<div className="empty">No revision notes yet. Add notes to a problem to keep key ideas handy.</div>}</>}
{page==='Analytics'&&<><div className="page-title"><div><div className="eyebrow">MEASURE YOUR MOMENTUM</div><h1>Progress analytics</h1><p>Use the patterns to decide what to practice next.</p></div></div><div className="stats"><Stat label="Problems solved" value={solved} sub="Completed" icon={CheckCircle2} tone="green"/><Stat label="In revision" value={revision} sub="Reinforce concepts" icon={RefreshCw} tone="purple"/><Stat label="Attempted" value={attempted} sub="Continue practicing" icon={CircleDashed} tone="orange"/><Stat label="Total problems" value={problems.length} sub="All records" icon={Code2} tone="blue"/></div><div className="grid"><section className="panel"><div className="panel-head"><div><h3>Weekly solved problems</h3><p>Solved problems over the last 7 days</p></div></div><div className="chart tall"><ResponsiveContainer width="100%" height="100%"><RBarChart data={week}><CartesianGrid stroke="#edf0f6" vertical={false}/><XAxis dataKey="day" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="solved" fill="#7667f5" radius={[5,5,0,0]}/></RBarChart></ResponsiveContainer></div></section><section className="panel"><div className="panel-head"><div><h3>Topic coverage</h3><p>Problems grouped by topic</p></div></div><div className="topic-list">{topics.map((t,i)=><div key={t.topic}><div className="topic-meta"><span>{t.topic}</span><b>{t.count}</b></div><div className="track"><i className={'color-'+i} style={{width:((t.count / Math.max(...topics.map(t => t.count), 1)) * 100)+'%'}}/></div></div>)}</div></section></div></>}
{page==='Settings'&&<><div className="page-title"><div><div className="eyebrow">MAKE CODETRACK YOURS</div><h1>Settings</h1><p>Manage your CodeTrack preferences and data.</p></div></div><section className="panel" style={{maxWidth:760,padding:24}}><div className="panel-head"><div><h3>Appearance</h3><p>Choose how the workspace behaves on this device.</p></div></div><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:20,padding:'18px 0',borderBottom:'1px solid #edf0f6'}}><div><b style={{display:'block',fontSize:14}}>Compact layout</b><small style={{color:'#9299ad'}}>Reduce spacing in lists and panels.</small></div><input aria-label="Compact layout" type="checkbox" checked={compactMode} onChange={e=>{setCompactMode(e.target.checked);document.body.classList.toggle('compact-mode',e.target.checked);notify(e.target.checked?'Compact layout enabled':'Compact layout disabled')}}/></div><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:20,padding:'18px 0',borderBottom:'1px solid #edf0f6'}}><div><b style={{display:'block',fontSize:14}}>In-app notifications</b><small style={{color:'#9299ad'}}>Show feedback messages after actions.</small></div><input aria-label="In-app notifications" type="checkbox" checked={showNotifications} onChange={e=>setShowNotifications(e.target.checked)}/></div><div style={{paddingTop:20}}><h3 style={{marginBottom:6}}>Local data</h3><p style={{ color: 'var(--muted)', lineHeight: 1.7 }}>
  Your problem records are stored in the CodeTrack backend and synced with your MySQL database.
</p></div></section></>}
{page==='Weekly goals'&&<><div className="page-title"><div><div className="eyebrow">CONSISTENCY OVER INTENSITY</div><h1>Weekly goals</h1><p>Set a manageable target and keep your streak moving.</p></div></div><section className="panel goal-detail"><div className="goal-big"><Target/></div><h2>Your weekly target</h2><p>Starter goal: track 25 problems per week.</p><div className="progress large">
  <i style={{ width: `${weeklyProgress}%` }} />
</div>

<div className="goal-numbers">
  <b>{weeklySolved} <span>/ {weeklyGoal} problems</span></b>
  <strong>{weeklyProgress}%</strong>
</div><p className="hint">This is a visual demo goal. Goal editing can be added later.</p></section></>}
</>
)}
</div></main>{modal&&<Modal title={edit?'Edit problem':'Add a problem'} onClose={()=>setModal(false)}><form className="form" onSubmit={submit}><label>Problem title *<input autoFocus required value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="e.g. Two Sum"/></label><div className="form-row"><label>Platform<select value={form.platform} onChange={e=>setForm({...form,platform:e.target.value})}><option>LeetCode</option><option>GeeksforGeeks</option><option>Codeforces</option><option>HackerRank</option><option>Other</option></select></label><label>Topic<select value={form.topic} onChange={e=>setForm({...form,topic:e.target.value})}><option>Arrays & Hashing</option><option>Strings</option><option>Two Pointers</option><option>Sliding Window</option><option>Linked List</option><option>Stack</option><option>Queue</option><option>Binary Search</option><option>Trees</option><option>Heap</option><option>Graphs</option><option>Dynamic Programming</option><option>Greedy</option><option>Backtracking</option><option>Other</option></select></label></div><div className="form-row"><label>Difficulty<select value={form.difficulty} onChange={e=>setForm({...form,difficulty:e.target.value})}><option>Easy</option><option>Medium</option><option>Hard</option></select></label><label>Status<select value={form.status} onChange={e=>setForm({...form,status:e.target.value})}><option>Solved</option><option>Attempted</option><option>Revision</option></select></label></div><div className="form-row"><label>Date practiced<input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})}/></label><label>Problem URL<input type="url" value={form.url} onChange={e=>setForm({...form,url:e.target.value})} placeholder="https://..."/></label></div><label>Revision notes<textarea rows="3" value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} placeholder="Key idea, mistake to avoid, or what to revise..."/></label><div className="form-actions"><button type="button" className="secondary" onClick={()=>setModal(false)}>Cancel</button><button type="submit" className="primary" disabled={saving}>
  <Check size={16}/>
  {saving ? 'Saving...' : edit ? 'Save changes' : 'Add problem'}
</button></div></form></Modal>}{profileOpen&&<Modal title="Your profile" onClose={()=>setProfileOpen(false)}><div style={{display:'flex',alignItems:'center',gap:14,padding:'8px 0 20px'}}><div className="avatar" style={{width:52,height:52,fontSize:20}}>Y</div><div><h3 style={{margin:'0 0 4px'}}>{currentUser?.name || 'CodeTrack account'}</h3><p style={{margin:0,color:'#9299ad',fontSize:13}}>{currentUser?.email}</p></div></div><div style={{background:'#f8f8fc',borderRadius:10,padding:14,marginBottom:18}}><b style={{fontSize:13}}>Profile status</b><p style={{margin:'6px 0 0',fontSize:13,color:'#9299ad'}}>Your problem records are stored in the CodeTrack backend.</p></div><div className="form-actions"><button className="secondary" onClick={()=>{setProfileOpen(false);setPage('Settings')}}><Settings size={15}/> Settings</button><button className="secondary" onClick={()=>{setProfileOpen(false);logout()}}>Log out</button><button className="primary" onClick={()=>setProfileOpen(false)}>Done</button></div></Modal>}{toast&&<div className="toast"><CheckCircle2 size={17}/>{toast}</div>}</div>
}
function ProblemTable({problems,onEdit,onDelete,onStatus,empty='No problems yet.'}){if(!problems.length)return <div className="table-empty"><Search size={22}/><p>{empty}</p></div>;return <div className="table-wrap"><table><thead><tr><th>PROBLEM</th><th>TOPIC</th><th>DIFFICULTY</th><th>STATUS</th><th>DATE</th><th/></tr></thead><tbody>{problems.map(p=><tr key={p.id}><td><div className="problem"><span className="problem-icon"><Code2 size={15}/></span><div><b>{p.title}</b><small>{p.platform}{p.url&&<> · <a href={p.url} target="_blank" rel="noreferrer">Open problem ↗</a></>}</small></div></div></td><td><span className="topic-pill">{p.topic}</span></td><td><span className={'difficulty '+p.difficulty.toLowerCase()}>{p.difficulty}</span></td><td><select className={'status '+p.status.toLowerCase()} value={p.status} onChange={e=>onStatus(p.id,e.target.value)}><option>Solved</option><option>Attempted</option><option>Revision</option></select></td><td className="date">{p.date}</td><td><div className="row-actions"><button title="Edit" onClick={()=>onEdit(p)}><Settings size={15}/></button><button title="Delete" onClick={()=>onDelete(p.id)}><Trash2 size={15}/></button></div></td></tr>)}</tbody></table></div>}
