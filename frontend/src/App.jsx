import React, { useState } from 'react';
import { LayoutGrid, MessageSquare, Clock, Settings, Activity } from 'lucide-react';
import HandoffQueue from './HandoffQueue';
import ConversationDetail from './ConversationDetail';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('queue');
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [activeRunData, setActiveRunData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const navigateToQueue = () => {
    setCurrentScreen('queue');
    setActiveRunData(null);
  };

  // This function actually calls your FastAPI backend
  const runLiveTest = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: `live_test_${Math.floor(Math.random() * 1000)}`,
          today: '2026-10-01',
          turns: [
            "Namaste, kal Dr. Rao free hain kya?",
            "Mera naam Rajesh Sharma hai, mujhe unse milna hai.",
            "Theek hai, book kar dijiye."
          ]
        })
      });

      if (!response.ok) throw new Error("Backend request failed");
      
      const data = await response.json();
      
      // Format the backend response to match our UI expectations
      const formattedData = {
        id: data.conversation_id,
        timestamp: new Date().toLocaleString(),
        terminal_state: data.terminal_state,
        escalation_reason: data.escalation_reason,
        patient_id: data.patient_id,
        appointment_id: data.appointment_id,
        metrics: data.metrics,
        turns: [
          { role: 'caller', text: "Namaste, kal Dr. Rao free hain kya?" },
          { role: 'caller', text: "Mera naam Rajesh Sharma hai, mujhe unse milna hai." },
          { role: 'caller', text: "Theek hai, book kar dijiye." },
          ...data.tool_calls.map(tc => ({
            role: 'tool',
            name: tc.name,
            args: tc.arguments,
            result: { status: 'executed' } // Backend doesn't return raw tool returns in the schema, just the calls
          })),
          { role: 'agent', text: data.reply }
        ]
      };

      setActiveRunData(formattedData);
      setCurrentScreen('detail');
    } catch (error) {
      alert("Failed to connect to backend. Is Uvicorn running? " + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-800">
      <div className="w-16 bg-white border-r border-slate-200 flex flex-col items-center py-4 space-y-8">
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mb-4 cursor-pointer" onClick={navigateToQueue}>
          S
        </div>
        <div className="flex flex-col space-y-6 text-slate-400">
          <LayoutGrid className="w-5 h-5 cursor-pointer hover:text-blue-600 transition-colors" onClick={navigateToQueue} />
          <MessageSquare className="w-5 h-5 cursor-pointer text-blue-600" />
          <Activity 
            className={`w-5 h-5 cursor-pointer transition-colors ${isLoading ? 'text-green-500 animate-pulse' : 'hover:text-blue-600'}`} 
            onClick={runLiveTest} 
            title="Run Live API Test"
          />
          <Settings className="w-5 h-5 cursor-pointer hover:text-blue-600 transition-colors" />
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {currentScreen === 'queue' ? (
          <HandoffQueue onSelectConversation={() => setCurrentScreen('detail')} />
        ) : (
          <ConversationDetail 
            conversationId={activeRunData?.id} 
            liveData={activeRunData} // We pass the real data down
            onBack={navigateToQueue} 
          />
        )}
      </div>
    </div>
  );
}