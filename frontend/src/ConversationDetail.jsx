import React from 'react';
import { ArrowLeft, Bot, User, CheckCircle2, ShieldAlert, Settings } from 'lucide-react';

export default function ConversationDetail({ conversationId, liveData, onBack }) {
  // Dummy data representing the expected format of a parsed conversation response
  // We will replace this with a real backend fetch once your new API key is ready.
  const conversation = liveData || {
    id: conversationId || 'cv_4471',
    timestamp: '11:42 AM · 2026-10-01',
    terminal_state: 'escalated',
    escalation_reason: 'clinical_urgent',
    patient_id: 'pt_0018',
    appointment_id: null,
    metrics: { turns: 3, tokens: 412, latency_ms: 1850 },
    turns: [
      { role: 'caller', text: 'Namaste, mujhe Dr. Rao se milna hai. Aaj hi milna padega.' },
      { role: 'agent', text: 'Namaste. Kya main aapka naam aur phone number jaan sakti hoon?' },
      { role: 'caller', text: 'Mera naam Sanjay Rawat hai. Seene mein bahut tez dard ho raha hai subah se.' },
      { 
        role: 'tool', 
        name: 'escalate_to_human', 
        args: { reason: 'clinical_urgent', detail: 'Patient reporting severe chest pain.' }, 
        result: { status: 'escalating', reason: 'clinical_urgent' } 
      }
    ]
  };

  const isEscalated = conversation.terminal_state === 'escalated';

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
        <div className="flex items-center space-x-4">
          <button onClick={onBack} className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-semibold font-mono text-slate-800">{conversation.id}</h1>
              {isEscalated ? (
                <span className="flex items-center space-x-1 rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                  <ShieldAlert className="h-3 w-3" />
                  <span>ESCALATED — CLINICAL</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1 rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                  <CheckCircle2 className="h-3 w-3" />
                  <span>{conversation.terminal_state.toUpperCase()}</span>
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 mt-1">Sunrise Clinic, Dehradun • {conversation.timestamp}</p>
          </div>
        </div>
        <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
          Take Over Chat
        </button>
      </div>

      {/* Main Content Split */}
      <div className="flex flex-1 overflow-hidden bg-slate-50">
        
        {/* Left Panel: Transcript */}
        <div className="flex-1 overflow-y-auto border-r border-slate-200 p-8">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-wider text-slate-500">Transcript</h2>
          <div className="space-y-6">
            {conversation.turns.map((turn, idx) => (
              <div key={idx} className={`flex ${turn.role === 'agent' || turn.role === 'tool' ? 'justify-end' : 'justify-start'}`}>
                {turn.role === 'caller' && (
                  <div className="mr-3 mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-500">
                    <User className="h-4 w-4" />
                  </div>
                )}
                
                <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                  turn.role === 'caller' ? 'bg-white text-slate-800 shadow-sm border border-slate-100' : 
                  turn.role === 'agent' ? 'bg-blue-600 text-white shadow-sm' : 
                  'bg-slate-800 text-slate-200 w-full font-mono text-xs'
                }`}>
                  {turn.role === 'tool' ? (
                    <div>
                      <div className="flex items-center space-x-2 text-slate-400 mb-2 border-b border-slate-700 pb-2">
                        <Settings className="h-3 w-3" />
                        <span className="uppercase tracking-wider">Tool Execution: {turn.name}</span>
                      </div>
                      <div className="mb-2">
                        <span className="text-slate-500">Arguments: </span>
                        <span className="text-emerald-400">{JSON.stringify(turn.args)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Return: </span>
                        <span className="text-blue-300">{JSON.stringify(turn.result)}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed">{turn.text}</p>
                  )}
                </div>

                {(turn.role === 'agent' || turn.role === 'tool') && (
                  <div className="ml-3 mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                    {turn.role === 'agent' ? <Bot className="h-4 w-4" /> : <Settings className="h-4 w-4" />}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel: Outcome & State */}
        <div className="w-80 overflow-y-auto bg-white p-8">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-wider text-slate-500">Outcome State</h2>
          
          <div className="space-y-6">
            <div>
              <p className="text-xs font-medium text-slate-400 mb-1">TERMINAL STATE</p>
              <p className="text-sm font-mono text-slate-800 font-semibold">{conversation.terminal_state}</p>
            </div>
            
            {conversation.escalation_reason && (
              <div>
                <p className="text-xs font-medium text-slate-400 mb-1">ESCALATION REASON</p>
                <p className="text-sm font-mono text-red-600 font-semibold">{conversation.escalation_reason}</p>
              </div>
            )}
            
            <div>
              <p className="text-xs font-medium text-slate-400 mb-1">PATIENT ID</p>
              <p className="text-sm font-mono text-slate-800">{conversation.patient_id || 'null'}</p>
            </div>
            
            <div>
              <p className="text-xs font-medium text-slate-400 mb-1">APPOINTMENT ID</p>
              <p className="text-sm font-mono text-slate-800">{conversation.appointment_id || 'null'}</p>
            </div>

            <div className="pt-6 border-t border-slate-100">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-4">Metrics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-400 mb-1">Turns</p>
                  <p className="text-sm font-mono font-medium">{conversation.metrics.turns}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Tokens</p>
                  <p className="text-sm font-mono font-medium">{conversation.metrics.tokens}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Latency</p>
                  <p className="text-sm font-mono font-medium">{conversation.metrics.latency_ms}ms</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Determinism</p>
                  <p className="text-sm font-mono font-medium text-green-600">STABLE</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}