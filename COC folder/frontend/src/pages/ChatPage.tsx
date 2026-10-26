import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, AlertTriangle, ChevronDown, User, RefreshCw, HelpCircle, Info } from 'lucide-react';
import { sendChatMessage } from '../api/chat';
import type { ChatResponse } from '../types/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content?: string;
  data?: ChatResponse;
  error?: string;
  timestamp: string;
}

const SAMPLE_QUERIES = [
  "What will it cost to grow tomato in Hambantota this Yala on 1.5 acres?",
  "I'm advising a farmer in Nuwara Eliya about potato for next season. Is it a good time to plant?",
  "Predict the cost for green chilli in Anuradhapura"
];

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content:
        "Ayubowan! I am your AI Agricultural Cost Advisory Assistant, powered by the local llama3.1:8b model and calibrated SO1 predictive cost models. Ask me any question about crop cultivation costs, water regimes, or season forecasts across Sri Lanka in plain language.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage(query);
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        content: response.narrative,
        data: response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      let errorText = err?.message || "Could not process your query.";
      if (err?.code === 'ECONNABORTED' || (err?.message && err.message.toLowerCase().includes('timeout'))) {
        errorText = "Request timed out waiting for the local model. The Ollama llama3.1:8b model runs on local CPU and may take 45–90 seconds to load and compute. Please verify Ollama is active and try again.";
      } else if (err?.response?.data?.detail) {
        errorText = err.response.data.detail;
      }
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: 'assistant',
        error: errorText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Shell Container */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm flex flex-col h-[calc(100vh-10.5rem)] max-w-4xl mx-auto overflow-hidden">
        {/* Chat Header */}
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70 backdrop-blur-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-md shadow-emerald-700/20">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">AgriCost AI Assistant</h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-mono font-semibold">
                  Ollama llama3.1:8b
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Natural Language Cost Intelligence & Calibrated Prediction Range
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                setMessages([
                  {
                    id: 'welcome',
                    sender: 'assistant',
                    content:
                      "Ayubowan! I am your AI Agricultural Cost Advisory Assistant, powered by the local llama3.1:8b model and calibrated SO1 predictive cost models. Ask me any question about crop cultivation costs, water regimes, or season forecasts across Sri Lanka in plain language.",
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                  }
                ])
              }
              title="Reset conversation"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 rounded-lg transition-colors text-xs flex items-center gap-1 font-medium"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4 bg-slate-50/40">
          {messages.map((msg) => {
            if (msg.sender === 'user') {
              return (
                <div key={msg.id} className="flex justify-end items-start gap-2.5">
                  <div className="max-w-xl bg-emerald-600 text-white p-3.5 sm:p-4 rounded-2xl rounded-tr-xs shadow-xs text-xs sm:text-sm leading-relaxed">
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <span className="block text-[10px] text-emerald-200 text-right mt-1.5 font-mono">
                      {msg.timestamp}
                    </span>
                  </div>
                  <div className="w-7 h-7 rounded-full bg-emerald-700 text-white flex items-center justify-center shrink-0 text-xs font-semibold">
                    <User className="w-3.5 h-3.5" />
                  </div>
                </div>
              );
            }

            // Assistant Message
            return (
              <div key={msg.id} className="flex items-start gap-3 max-w-2xl">
                <div className="w-8 h-8 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 text-xs font-bold font-mono shadow-xs">
                  <Bot className="w-4 h-4 text-emerald-700" />
                </div>
                <div className="flex-1 bg-white p-4 rounded-2xl rounded-tl-xs border border-slate-200/80 shadow-xs text-xs sm:text-sm text-slate-800 space-y-3 leading-relaxed">
                  {/* Error State */}
                  {msg.error ? (
                    <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 space-y-1">
                      <div className="flex items-center gap-1.5 font-bold text-xs text-rose-900">
                        <AlertTriangle className="w-4 h-4 text-rose-600" />
                        <span>Query Could Not Be Processed</span>
                      </div>
                      <p className="text-xs">{msg.error}</p>
                    </div>
                  ) : (
                    <>
                      {/* Low Confidence Pill if flagged */}
                      {msg.data?.prediction.low_confidence && (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-300">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          <span>Low confidence prediction</span>
                        </div>
                      )}

                      {/* Lag Saturation Amber Callout */}
                      {msg.data?.prediction.lag_saturation_detected && (
                        <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-start gap-2 shadow-xs">
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                          <div className="leading-relaxed font-normal">
                            <span className="font-semibold text-amber-950">⚠️ Prior cost exceeds the model's training range. </span>
                            This prediction is a ceiling estimate (capped at Rs {msg.data.prediction.lag_saturation_threshold ? Math.round(msg.data.prediction.lag_saturation_threshold).toLocaleString() : ''}).
                          </div>
                        </div>
                      )}

                      {/* Plain-Language Narrative Paragraph */}
                      <p className="whitespace-pre-wrap leading-relaxed text-slate-700 font-normal">
                        {msg.content}
                      </p>

                      {/* Structured Prediction Data Dropdown */}
                      {msg.data && (
                        <details className="group mt-3 pt-3 border-t border-slate-100 text-xs">
                          <summary className="cursor-pointer font-semibold text-slate-600 hover:text-emerald-700 flex items-center justify-between select-none list-none py-1">
                            <span className="flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                              View structured data
                            </span>
                            <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180 text-slate-400" />
                          </summary>

                          <div className="mt-3 space-y-3 pt-2">
                            {/* Parsed Input Table */}
                            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/70">
                              <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2 font-mono">
                                Extracted Parameters
                              </h4>
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                                <div>
                                  <span className="text-slate-400 block text-[10px]">Crop</span>
                                  <span className="font-semibold text-slate-800">
                                    {msg.data.parsed_input.crop || 'Unspecified'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-400 block text-[10px]">District</span>
                                  <span className="font-semibold text-slate-800">
                                    {msg.data.parsed_input.district || 'Unspecified'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-400 block text-[10px]">Season</span>
                                  <div className="flex items-center gap-1.5 flex-wrap">
                                    <span className="font-semibold text-slate-800">
                                      {msg.data.parsed_input.season || 'Maha (default)'}
                                    </span>
                                    {msg.data.parsed_input.season_inferred && (
                                      <span
                                        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs"
                                        title="Assumed based on current calendar date"
                                      >
                                        <Info className="w-2.5 h-2.5 text-blue-600" />
                                        Inferred
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <div>
                                  <span className="text-slate-400 block text-[10px]">Water Regime</span>
                                  <span className="font-semibold text-slate-800">
                                    {msg.data.parsed_input.irrigation_type || 'Irrigated (default)'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-400 block text-[10px]">Field Size</span>
                                  <span className="font-semibold text-slate-800">
                                    {msg.data.parsed_input.field_size_acres
                                      ? `${msg.data.parsed_input.field_size_acres} acre(s)`
                                      : '1.0 acre (standard)'}
                                  </span>
                                </div>
                              </div>

                              {/* Prev Season Cost Row with Source Badge */}
                              {(() => {
                                const prevCostUsed = msg.data.prev_season_cost_used ?? msg.data.parsed_input.prev_season_cost;
                                const prevCostSource = msg.data.prev_season_cost_source || msg.data.parsed_input.prev_season_cost_source || (prevCostUsed ? 'officer_provided' : 'unavailable');
                                return (
                                  <div className="mt-2.5 pt-2.5 border-t border-slate-200/70 flex flex-wrap items-center justify-between gap-2">
                                    <div>
                                      <span className="text-slate-400 block text-[10px]">Prev Season Cost</span>
                                      <span className="font-semibold text-slate-800 text-xs">
                                        {prevCostUsed !== null && prevCostUsed !== undefined
                                          ? `Rs ${Math.round(prevCostUsed).toLocaleString()} LKR / acre`
                                          : 'Not available (using crop median)'}
                                      </span>
                                    </div>
                                    <div>
                                      {prevCostSource === 'auto_filled_from_history' && (
                                        <div className="flex items-center gap-1.5 flex-wrap">
                                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs">
                                            <Info className="w-3 h-3 text-blue-600 shrink-0" />
                                            Auto-filled from history
                                          </span>
                                          {(() => {
                                            const sYr = msg.data.prev_season_cost_source_year ?? msg.data.parsed_input.prev_season_cost_source_year;
                                            const sSea = msg.data.prev_season_cost_source_season ?? msg.data.parsed_input.prev_season_cost_source_season;
                                            if (sYr || sSea) {
                                              return (
                                                <span className="text-[11px] text-slate-500 font-medium">
                                                  (from {[sYr, sSea].filter(Boolean).join(' ')})
                                                </span>
                                              );
                                            }
                                            return null;
                                          })()}
                                        </div>
                                      )}
                                      {prevCostSource === 'officer_provided' && (
                                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 shadow-2xs">
                                          Provided by you
                                        </span>
                                      )}
                                      {prevCostSource === 'unavailable' && (
                                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-300 shadow-2xs">
                                          <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                                          Not available — using crop median
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                );
                              })()}
                            </div>

                            {/* Prediction Result Table */}
                            <div className="bg-emerald-50/50 p-3 rounded-xl border border-emerald-200/60">
                              <h4 className="text-[11px] font-bold text-emerald-900 uppercase tracking-wider mb-2 font-mono">
                                SO1 Calibrated Prediction Result
                              </h4>
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                <div>
                                  <span className="text-emerald-700/80 block text-[10px]">Predicted Cost</span>
                                  <span className="font-bold text-emerald-900 text-sm">
                                    Rs {msg.data.prediction.predicted_cost.toLocaleString()}
                                  </span>
                                  <span className="text-[9px] text-slate-400 block">per acre</span>
                                </div>
                                <div>
                                  <span className="text-emerald-700/80 block text-[10px]">80% Low</span>
                                  <span className="font-semibold text-slate-700">
                                    Rs {msg.data.prediction.interval_low.toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-emerald-700/80 block text-[10px]">80% High</span>
                                  <span className="font-semibold text-slate-700">
                                    Rs {msg.data.prediction.interval_high.toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-emerald-700/80 block text-[10px]">Confidence</span>
                                  <span
                                    className={`font-semibold ${
                                      msg.data.prediction.low_confidence ? 'text-amber-700' : 'text-emerald-700'
                                    }`}
                                  >
                                    {msg.data.prediction.low_confidence ? 'Low' : 'Standard'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </details>
                      )}
                    </>
                  )}

                  <span className="block text-[10px] text-slate-400 font-mono pt-1">
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            );
          })}

          {/* Three-Dot Loading State */}
          {isLoading && (
            <div className="flex items-start gap-3 max-w-md animate-in fade-in duration-200">
              <div className="w-8 h-8 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 text-xs font-bold font-mono shadow-xs">
                <Bot className="w-4 h-4 text-emerald-700 animate-pulse" />
              </div>
              <div className="bg-white px-4 py-3 rounded-2xl rounded-tl-xs border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-700 font-semibold">Assistant is thinking</span>
                  <span className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-bounce"></span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Parsing query & predicting cost via local model (takes ~30–60s on CPU)...
                </p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Starter Chips */}
        {messages.length <= 2 && (
          <div className="px-5 py-2 bg-slate-50/80 border-t border-slate-100 flex items-center gap-2 overflow-x-auto text-xs no-scrollbar">
            <span className="text-slate-400 font-mono text-[10px] shrink-0 flex items-center gap-1">
              <HelpCircle className="w-3 h-3" /> Sample questions:
            </span>
            {SAMPLE_QUERIES.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={isLoading}
                className="shrink-0 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-emerald-700 hover:border-emerald-300 hover:bg-emerald-50/40 text-[11px] transition-colors truncate max-w-xs"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="p-3 sm:p-4 border-t border-slate-200 bg-white">
          <div className="relative flex items-end gap-2">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask about crop costs, seasons, or districts (e.g. 'Cost to grow tomato in Hambantota this Yala on 1.5 acres?')..."
              className="flex-1 max-h-32 min-h-[44px] py-2.5 pl-4 pr-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-xs sm:text-sm text-slate-800 placeholder-slate-400 resize-none disabled:bg-slate-100 disabled:cursor-not-allowed leading-relaxed"
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !inputText.trim()}
              className="h-[44px] px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-200 text-white disabled:text-slate-400 flex items-center justify-center shrink-0 transition-all font-semibold shadow-xs disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 text-[10px] text-slate-400 px-1">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <span className="font-mono">Local LLM: llama3.1:8b (Offline & Private)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
