import React from 'react';

// Hardcoded mock data based on the required schema
const mockHandoffs = [
  { id: 'cv_4471', caller_said: '"Seene mein dard ho raha hai"', reason: 'clinical_urgent', reasonLabel: 'CLINICAL', time: '11:42' },
  { id: 'cv_4468', caller_said: 'Cancel for a different patient', reason: 'not_authorised', reasonLabel: 'NOT AUTHORISED', time: '11:20' },
  { id: 'cv_4463', caller_said: '"Sharma ji ke liye" — 3 matches', reason: 'ambiguous_patient', reasonLabel: 'AMBIGUOUS PATIENT', time: '10:57' },
  { id: 'cv_4455', caller_said: '"Ye dawai lun ya nahi?"', reason: 'medical_advice', reasonLabel: 'MEDICAL ADVICE', time: '10:18' }
];

export default function HandoffQueue({ onSelectConversation }) {
  const getBadgeColor = (reason) => {
    if (reason === 'clinical_urgent') return 'bg-red-100 text-red-700';
    if (reason === 'not_authorised') return 'bg-orange-100 text-orange-700';
    if (reason === 'ambiguous_patient') return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-50 text-red-600';
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Handoff Queue</h1>
          <p className="text-sm text-slate-500">Sunrise Clinic, Dehradun — Conversations the agent escalated</p>
        </div>
        <div className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-md">4 OPEN</div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs font-semibold text-slate-400 tracking-wider mb-2">CONVERSATIONS</p>
          <p className="text-2xl font-bold">37</p>
          <p className="text-xs text-slate-400 mt-1">Today</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs font-semibold text-slate-400 tracking-wider mb-2">COMPLETED BY AGENT</p>
          <p className="text-2xl font-bold">31</p>
          <p className="text-xs text-slate-400 mt-1">84%</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs font-semibold text-slate-400 tracking-wider mb-2">ESCALATED</p>
          <p className="text-2xl font-bold">6</p>
          <p className="text-xs text-blue-500 mt-1">4 still open</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs font-semibold text-slate-400 tracking-wider mb-2">URGENT</p>
          <p className="text-2xl font-bold">1</p>
          <p className="text-xs text-red-500 mt-1">clinical: unresolved</p>
        </div>
      </div>

      {/* Handoffs Table */}
      <h2 className="text-lg font-semibold mb-4">Open handoffs</h2>
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500 border-b border-slate-100">
            <tr>
              <th className="px-6 py-3 font-medium">CONVERSATION</th>
              <th className="px-6 py-3 font-medium">CALLER SAID</th>
              <th className="px-6 py-3 font-medium">REASON</th>
              <th className="px-6 py-3 font-medium">TIME</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {mockHandoffs.map((handoff) => (
              <tr key={handoff.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">{handoff.id}</td>
                <td className="px-6 py-4 text-slate-800">{handoff.caller_said}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getBadgeColor(handoff.reason)}`}>
                    {handoff.reasonLabel}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-500">{handoff.time}</td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => onSelectConversation(handoff.id)}
                    className="px-4 py-1.5 bg-blue-50 text-blue-600 font-medium rounded hover:bg-blue-100 transition-colors"
                  >
                    Resolve
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}