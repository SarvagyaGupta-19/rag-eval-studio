"use client";

import React, { useState, useRef, useEffect } from "react";
import { Zap, Send, FileIcon, CheckCircle2, AlertTriangle, XCircle, Brain, ChevronDown, CloudUpload, Plus } from "lucide-react";
import { ChatbotCharacter } from "@/components/ChatbotCharacter";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  faithfulnessScore?: number | null;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDeepThinking, setIsDeepThinking] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isHoveringInput, setIsHoveringInput] = useState(false);
  const [isHoveringAttach, setIsHoveringAttach] = useState(false);
  const [isHoveringDeep, setIsHoveringDeep] = useState(false);
  const [justFinished, setJustFinished] = useState(false);
  const [attachedFilename, setAttachedFilename] = useState<string | null>(null);
  const [isAppLoading, setIsAppLoading] = useState(true);
  const [loadingMood, setLoadingMood] = useState<any>("watching");
  const [spinRot, setSpinRot] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Start the smooth spin animation right after mount
    setTimeout(() => setSpinRot(1080), 50);

    // After 2.2s (when the spin finishes), show the joy reaction
    const timer1 = setTimeout(() => {
      setLoadingMood("joy");
    }, 2200);

    // After 3.2s, dismiss the loading screen
    const timer2 = setTimeout(() => {
      setIsAppLoading(false);
    }, 3200);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleNewChat = () => {
    setMessages([]);
    setPrompt("");
    setAttachedFilename(null);
    setUploadStatus(null);
    setUploadProgress(null);
  };

  const getBotMood = (): any => {
    if (uploadStatus?.includes("Error") || uploadStatus?.includes("failed")) return "upset";
    if (uploadStatus?.includes("Successfully") || uploadStatus?.includes("processed")) return "joy";
    if (uploadStatus) return "confusion";

    if (isLoading) {
      if (isDeepThinking) return "confusion";
      return "sly";
    }

    if (justFinished) return "joy";

    if (isHoveringDeep) return "confusion";
    if (isHoveringAttach) return "friendly";
    
    if (prompt.length > 50) return "sly";
    if (prompt.length > 0 || isHoveringInput) return "watching";

    return "watching";
  };
  const currentMood = getBotMood();

  const handleSend = async () => {
    if (!prompt.trim() || isLoading) return;
    
    const userMsg = prompt;
    const filter = attachedFilename;
    setPrompt("");
    setAttachedFilename(null);
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMsg, source_filter: filter }),
      });

      if (!res.ok) throw new Error("Failed to fetch response");

      const data = await res.json();
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        faithfulnessScore: data.faithfulness_score
      }]);
      setJustFinished(true);
      setTimeout(() => setJustFinished(false), 3000);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I'm sorry, I encountered an error while processing your request. Please ensure the backend is running."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus(`Uploading ${file.name}...`);
    setUploadProgress(0);
    
    // Fake progress animation for a realistic feel
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev === null) return null;
        if (prev >= 90) return 90; // Stall at 90% until backend responds
        return prev + Math.random() * 15;
      });
    }, 200);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/upload`, {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);

      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      
      setUploadProgress(100);
      setUploadStatus(`Successfully processed`);
      setAttachedFilename(file.name);
      
      setTimeout(() => {
        setUploadStatus(null);
        setUploadProgress(null);
      }, 3000);
    } catch (error) {
      clearInterval(progressInterval);
      setUploadProgress(null);
      setUploadStatus("Error uploading file. Please ensure backend is running.");
      setTimeout(() => setUploadStatus(null), 5000);
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getScoreColor = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "text-gray-400";
    if (score >= 0.7) return "text-blue-400";
    if (score >= 0.4) return "text-orange-400";
    return "text-red-400";
  };

  const getScoreIcon = (score: number | null | undefined) => {
    if (score === null || score === undefined) return null;
    if (score >= 0.7) return <CheckCircle2 size={14} className="text-blue-400 mr-1" />;
    if (score >= 0.4) return <AlertTriangle size={14} className="text-orange-400 mr-1" />;
    return <XCircle size={14} className="text-red-400 mr-1" />;
  };

  // Reusable input component for both centered (empty) and bottom (chatting) states
  const inputComponent = (
    <div 
      className={`w-full max-w-2xl relative group rounded-[24px] overflow-hidden p-[1.5px] shadow-[0_0_25px_rgba(168,85,247,0.1)] transition-all duration-500 pointer-events-auto ${uploadProgress !== null ? 'ring-2 ring-blue-500/50' : 'hover:shadow-[0_0_35px_rgba(168,85,247,0.2)]'}`}
      onMouseEnter={() => setIsHoveringInput(true)}
      onMouseLeave={() => setIsHoveringInput(false)}
    >
      {/* Animated Rotating Light Border */}
      <div className={`absolute inset-[-100%] ${uploadProgress !== null ? 'bg-cyan-500/50 animate-pulse' : 'animate-[spin_4s_linear_infinite] bg-[conic-gradient(from_90deg,transparent_0%,transparent_70%,rgba(168,85,247,0.8)_85%,rgba(56,189,248,0.8)_100%)]'}`}></div>
      
      {/* Inner Dark Container */}
      <div className="relative w-full h-full rounded-[22.5px] bg-[#09090b] flex flex-col p-1.5 shadow-inner overflow-hidden">
        
        {/* Real Uploading Progress Bar Background */}
        {uploadProgress !== null && (
          <div 
            className="absolute top-0 left-0 h-full bg-purple-600/20 transition-all duration-300 ease-out z-0"
            style={{ width: `${uploadProgress}%` }}
          >
            {/* Glossy overlay for realism */}
            <div className="absolute top-0 right-0 bottom-0 w-20 bg-gradient-to-r from-transparent to-purple-400/40 blur-sm"></div>
          </div>
        )}

        <div className="relative z-10 flex flex-col w-full h-full">
          
          {/* Attached File Preview Chip */}
          {attachedFilename && uploadProgress === null && (
            <div className="flex items-center space-x-2 bg-purple-500/10 border border-purple-500/30 text-purple-200 px-3 py-1.5 rounded-lg mx-3 mt-3 w-fit text-xs animate-fade-in shadow-[0_0_15px_rgba(168,85,247,0.15)]">
              <FileIcon size={14} className="text-purple-400" />
              <span className="font-medium tracking-wide">{attachedFilename}</span>
              <button 
                onClick={() => setAttachedFilename(null)} 
                className="ml-1 text-purple-400/60 hover:text-white transition-colors"
              >
                <XCircle size={14} />
              </button>
            </div>
          )}

          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={uploadProgress !== null ? `Uploading document... ${Math.round(uploadProgress)}%` : "How can I help you?"}
            className="w-full bg-transparent text-gray-100 px-3 pt-2 pb-2 outline-none placeholder:text-[#6b6b75] font-light text-[15px]"
            disabled={isLoading || uploadProgress !== null}
          />
        
        <div className="flex items-center justify-between px-1 pb-1 pt-1.5">
          <div className="flex items-center space-x-2">
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              className="hidden" 
              accept=".pdf"
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              onMouseEnter={() => setIsHoveringAttach(true)}
              onMouseLeave={() => setIsHoveringAttach(false)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-[#18181b] hover:bg-[#27272a] text-gray-200 transition-colors text-sm border border-[#27272a]"
            >
              <CloudUpload size={16} />
              <span>Attach files</span>
            </button>
            <button 
              onClick={() => setIsDeepThinking(!isDeepThinking)}
              onMouseEnter={() => setIsHoveringDeep(true)}
              onMouseLeave={() => setIsHoveringDeep(false)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full transition-all text-sm border ${
                isDeepThinking 
                  ? "bg-[#18181b] text-purple-400 border-purple-500/30 shadow-[0_0_10px_rgba(168,85,247,0.2)]" 
                  : "bg-[#18181b] hover:bg-[#27272a] text-gray-200 border-[#27272a]"
              }`}
            >
              <Brain size={16} className={isDeepThinking ? "animate-pulse" : ""} />
              <span>Deep thinking</span>
              <ChevronDown size={12} className="ml-0.5 opacity-60" />
            </button>
          </div>
          <button 
            onClick={handleSend}
            disabled={!prompt.trim() || isLoading}
            className="w-[30px] h-[30px] rounded-full flex items-center justify-center text-gray-200 bg-[#09090b] transition-all disabled:opacity-30 disabled:cursor-not-allowed border-[1.5px] border-[#38bdf8] hover:bg-cyan-500/20 mr-1"
          >
            <Send size={13} className="-ml-0.5" />
          </button>
        </div>
        </div>
      </div>
    </div>
  );



  return (
    <main className="h-screen flex flex-col relative overflow-hidden">
      {/* Background Effect - Halftone Matrix Pattern */}
      <div className="bg-halftone-fixed z-0"></div>

      {/* Seamless Loading Overlay */}
      <div 
        className={`absolute inset-0 z-50 flex flex-col items-center justify-center transition-all duration-1000 ease-in-out ${
          isAppLoading ? "opacity-100 backdrop-blur-sm" : "opacity-0 pointer-events-none backdrop-blur-none"
        }`}
      >
        <div className={`z-20 flex flex-col items-center justify-center transition-all duration-1000 ease-in-out transform ${
          isAppLoading ? "scale-100 translate-y-0" : "scale-50 -translate-y-20 opacity-0"
        }`}>
          <div 
            className="transition-transform duration-[2200ms] ease-in-out" 
            style={{ transform: `rotate(${spinRot}deg)` }}
          >
            <ChatbotCharacter mood={loadingMood} className="w-64 h-64 drop-shadow-[0_0_25px_rgba(56,189,248,0.5)]" />
          </div>
        </div>
      </div>

      {/* Header - Fixed at top */}
      <div className="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-6 border-b border-white/5 bg-black/10 backdrop-blur-md z-20">
        <div className="flex items-center space-x-2">
          <ChatbotCharacter mood={currentMood} className="w-10 h-10 -ml-1" />
          <h1 className="text-lg font-medium text-white tracking-wide">RAG Eval Studio</h1>
        </div>
        <div className="flex items-center space-x-3">
          {uploadStatus && uploadProgress === null && (
            <div className="text-sm px-3 py-1 bg-white/10 rounded-full text-white/80 flex items-center animate-pulse border border-white/20">
              <FileIcon size={14} className="mr-2 text-orange-400" /> {uploadStatus}
            </div>
          )}
          {messages.length > 0 && (
            <button 
              onClick={handleNewChat}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-full text-sm text-gray-300 transition-all shadow-sm"
            >
              <Plus size={14} />
              <span>New Chat</span>
            </button>
          )}
        </div>
      </div>

      {messages.length === 0 ? (
        /* --- EMPTY STATE: CENTERED SEARCH BAR --- */
        <div className="flex-1 flex flex-col items-center justify-center w-full h-full relative z-10 px-4">
          <div className="w-full flex flex-col items-center justify-center z-20 pointer-events-auto pb-10">
            
            {/* Animated Chatbot Mascot */}
            <div className="flex items-center justify-center mb-8 mt-4 h-48 md:h-64">
              <ChatbotCharacter mood={currentMood} className="w-48 md:w-64" />
            </div>

            <h2 className="text-3xl md:text-4xl font-light text-white mb-8 tracking-wide drop-shadow-md">How can I help you?</h2>
            {inputComponent}
            <div className="text-center mt-4 text-sm text-gray-400 font-light tracking-wide bg-transparent pointer-events-auto">
              RAG Eval Studio can make mistakes. Always verify output from the data space.
            </div>
          </div>

        </div>
      ) : (
        /* --- CHAT STATE: MESSAGES & BOTTOM SEARCH BAR --- */
        <>
          <div className="flex-1 w-full max-w-4xl mx-auto flex flex-col relative z-10 pt-24 pb-32 overflow-y-auto px-4 md:px-8 custom-scrollbar">
            <div className="space-y-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`flex items-start ${msg.role === "assistant" ? "max-w-[90%]" : "max-w-[80%]"}`}>
                    {msg.role === "assistant" && (
                      <ChatbotCharacter mood="friendly" className="w-8 h-8 mr-3 mt-1 flex-shrink-0 drop-shadow-[0_0_8px_rgba(59,130,246,0.3)]" />
                    )}
                    <div className={`rounded-2xl px-5 py-3.5 ${
                      msg.role === "user" 
                        ? "bg-purple-600/60 backdrop-blur-md text-white shadow-[0_0_20px_rgba(168,85,247,0.2)] border border-purple-500/50" 
                        : "bg-[#18181b]/90 backdrop-blur-md text-gray-100 border border-white/10 shadow-lg"
                    }`}>
                      <div className="leading-relaxed whitespace-pre-wrap font-light">{msg.content}</div>
                    </div>
                  </div>
                  
                  {msg.role === "assistant" && (msg.sources || msg.faithfulnessScore !== undefined) && (
                    <div className="mt-2 flex flex-wrap gap-2 px-2 items-center">
                      {msg.sources && msg.sources.map((source, sIdx) => (
                        <span key={sIdx} className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10 shadow-sm">
                          {source}
                        </span>
                      ))}
                      {msg.faithfulnessScore !== null && msg.faithfulnessScore !== undefined && (
                        <span className={`text-xs px-2.5 py-1 rounded-full bg-white/5 border border-white/10 shadow-sm flex items-center ${getScoreColor(msg.faithfulnessScore)}`}>
                          {getScoreIcon(msg.faithfulnessScore)}
                          Confidence: {msg.faithfulnessScore}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
              
              {isLoading && (
                <div className="flex items-start max-w-[90%]">
                  <ChatbotCharacter mood="friendly" className="w-8 h-8 mr-3 mt-1 flex-shrink-0 drop-shadow-[0_0_8px_rgba(59,130,246,0.3)] animate-pulse" />
                  <div className="rounded-2xl px-5 py-4 bg-[#18181b]/90 backdrop-blur-md border border-white/10 flex space-x-2 items-center shadow-lg">
                    <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce"></div>
                    <div className="w-2 h-2 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: "0.15s" }}></div>
                    <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "0.3s" }}></div>
                    <span className="text-sm text-gray-300 ml-2 font-light">Navigating data space...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-black/80 to-transparent flex flex-col items-center z-20 pointer-events-none">
            {inputComponent}
            <div className="text-center mt-3 mb-1 text-[13px] text-gray-400 font-light tracking-wide bg-transparent pointer-events-auto">
              RAG Eval Studio can make mistakes. Always verify output from the data space.
            </div>
          </div>
        </>
      )}
    </main>
  );
}
