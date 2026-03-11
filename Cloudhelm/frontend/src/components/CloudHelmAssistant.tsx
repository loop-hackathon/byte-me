import { useState, useEffect } from 'react';
import { X, Send, Sparkles, Users, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'message' | 'question' | 'task_delegation' | 'task_status';
  metadata?: any;
}

interface InteractiveQuestion {
  question: string;
  options: Array<{
    label: string;
    description: string;
  }>;
}

interface TaskInfo {
  task_id: string;
  description: string;
  agent_type: string;
  status: string;
}

interface CloudHelmAssistantProps {
  repositoryId?: string;
  repositoryName?: string;
}

export default function CloudHelmAssistant({ repositoryId, repositoryName }: CloudHelmAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTasks, setActiveTasks] = useState<TaskInfo[]>([]);
  const [availableAgents, setAvailableAgents] = useState<any>({});
  const [showTaskPanel, setShowTaskPanel] = useState(false);

  // Load active tasks and available agents when component opens
  useEffect(() => {
    if (isOpen) {
      loadActiveTasks();
      loadAvailableAgents();
    }
  }, [isOpen]);

  const loadActiveTasks = async () => {
    try {
      const response = await api.listActiveTasks();
      setActiveTasks(response.active_tasks || []);
    } catch (error) {
      console.error('Error loading active tasks:', error);
    }
  };

  const loadAvailableAgents = async () => {
    try {
      const response = await api.getAvailableAgents();
      setAvailableAgents(response.agents || {});
    } catch (error) {
      console.error('Error loading available agents:', error);
    }
  };

  // Helper to render message content with enhanced markdown support and interactive elements
  const renderMessageContent = (message: Message) => {
    const { content, type, metadata } = message;
    
    // Handle interactive questions
    if (type === 'question' && metadata?.questions) {
      return (
        <div className="space-y-4">
          <div className="text-sm text-zinc-300">{content}</div>
          {metadata.questions.map((q: InteractiveQuestion, qIndex: number) => (
            <div key={qIndex} className="bg-zinc-800/30 rounded-lg p-3 border border-zinc-700/50">
              <h4 className="text-sm font-medium text-white mb-2">{q.question}</h4>
              <div className="space-y-2">
                {q.options.map((option, oIndex) => (
                  <button
                    key={oIndex}
                    onClick={() => handleQuestionResponse(qIndex, oIndex, option.label)}
                    className="w-full text-left p-2 bg-zinc-700/30 hover:bg-zinc-700/50 rounded border border-zinc-600/30 hover:border-zinc-500/50 transition-colors"
                  >
                    <div className="text-xs font-medium text-cyan-400">{option.label}</div>
                    <div className="text-xs text-zinc-400">{option.description}</div>
                  </button>
                ))}
                <button
                  onClick={() => handleQuestionResponse(qIndex, -1, 'Other')}
                  className="w-full text-left p-2 bg-zinc-700/30 hover:bg-zinc-700/50 rounded border border-zinc-600/30 hover:border-zinc-500/50 transition-colors"
                >
                  <div className="text-xs font-medium text-cyan-400">Other</div>
                  <div className="text-xs text-zinc-400">Provide your own answer</div>
                </button>
              </div>
            </div>
          ))}
        </div>
      );
    }
    
    // Handle task delegation status
    if (type === 'task_delegation' && metadata?.task_id) {
      return (
        <div className="space-y-3">
          <div className="text-sm text-zinc-300">{content}</div>
          <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-medium text-indigo-300">Task Delegated</span>
            </div>
            <div className="text-xs text-zinc-400">
              <div>Task ID: <code className="text-cyan-400">{metadata.task_id}</code></div>
              <div>Agent: <span className="text-indigo-300">{metadata.agent_type}</span></div>
            </div>
            <button
              onClick={() => checkTaskStatus(metadata.task_id)}
              className="mt-2 text-xs text-indigo-400 hover:text-indigo-300 underline"
            >
              Check Status
            </button>
          </div>
        </div>
      );
    }
    
    // Regular message content with code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        // Code block
        const code = part.slice(3, -3).trim();
        return (
          <pre key={index} className="bg-black/30 rounded p-2 my-2 overflow-x-auto text-xs">
            <code className="text-green-400">{code}</code>
          </pre>
        );
      } else {
        // Regular text with inline code
        const textParts = part.split(/(`[^`]+`)/g);
        return (
          <span key={index}>
            {textParts.map((textPart, i) => {
              if (textPart.startsWith('`') && textPart.endsWith('`')) {
                return (
                  <code key={i} className="bg-black/30 px-1.5 py-0.5 rounded text-xs text-cyan-400">
                    {textPart.slice(1, -1)}
                  </code>
                );
              }
              return <span key={i}>{textPart}</span>;
            })}
          </span>
        );
      }
    });
  };

  const handleQuestionResponse = async (_questionIndex: number, _optionIndex: number, response: string) => {
    const userMessage: Message = {
      role: 'user',
      content: `Selected: ${response}`,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send the response back to the assistant
      const apiResponse = await api.queryAssistant({
        repository_id: repositoryId,
        repository_name: repositoryName,
        query: `User selected: ${response}. Please continue with guidance based on this choice.`,
        context_type: 'general',
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: apiResponse.response,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Error sending question response:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error processing your response: ${error.message || 'Unknown error'}`,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const checkTaskStatus = async (taskId: string) => {
    try {
      const status = await api.getTaskStatus(taskId);
      
      const statusMessage: Message = {
        role: 'system',
        content: `Task ${taskId} Status: ${status.status}${status.result ? `\n\nResult: ${status.result.substring(0, 500)}...` : ''}${status.error ? `\n\nError: ${status.error}` : ''}`,
        timestamp: new Date(),
        type: 'task_status',
        metadata: status
      };
      
      setMessages(prev => [...prev, statusMessage]);
      
      // Refresh active tasks
      loadActiveTasks();
    } catch (error: any) {
      console.error('Error checking task status:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // Check if this is a task delegation command
      if (currentInput.startsWith('/task ')) {
        const taskDescription = currentInput.substring(6).trim();
        
        // Try to delegate the task
        try {
          const delegationResponse = await api.delegateTask({
            task_description: taskDescription,
            agent_type: 'explore', // Default, will be determined by backend
            repository_name: repositoryName || 'Unknown Repository',
          });
          
          const taskMessage: Message = {
            role: 'assistant',
            content: `🤖 **Task Delegated Successfully**\n\nI've assigned this task to a specialized subagent.\n\n**Task ID:** \`${delegationResponse.task_id}\`\n**Description:** ${taskDescription}\n\nThe subagent is working on this independently. You can check the progress or continue with other tasks.`,
            timestamp: new Date(),
            type: 'task_delegation',
            metadata: {
              task_id: delegationResponse.task_id,
              agent_type: 'subagent',
              description: taskDescription
            }
          };
          
          setMessages(prev => [...prev, taskMessage]);
          loadActiveTasks(); // Refresh active tasks
          return;
        } catch (delegationError) {
          // Fall back to regular query if delegation fails
          console.warn('Task delegation failed, falling back to regular query:', delegationError);
        }
      }

      // Regular assistant query
      const response = await api.queryAssistant({
        repository_id: repositoryId,
        repository_name: repositoryName,
        query: currentInput,
        context_type: 'general',
      });

      // Check if response contains interactive questions
      const questionPattern = /🤔.*I need your input.*Question \d+:/s;
      if (questionPattern.test(response.response)) {
        // Parse interactive questions from response
        const questions = parseInteractiveQuestions(response.response);
        
        if (questions.length > 0) {
          const questionMessage: Message = {
            role: 'assistant',
            content: response.response,
            timestamp: new Date(),
            type: 'question',
            metadata: { questions }
          };
          
          setMessages(prev => [...prev, questionMessage]);
          return;
        }
      }

      // Regular assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message || 'Failed to get response'}. Please make sure MISTRAL_API_KEY is configured in the backend.`,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const parseInteractiveQuestions = (response: string): InteractiveQuestion[] => {
    // Simple parser for interactive questions
    // This is a basic implementation - in a real app you'd want more robust parsing
    const questions: InteractiveQuestion[] = [];
    
    try {
      const questionMatches = response.match(/\*\*Question \d+:\*\* (.+?)\n\n((?:\d+\. \*\*[^*]+\*\* - [^\n]+\n?)+)/g);
      
      if (questionMatches) {
        questionMatches.forEach(match => {
          const questionMatch = match.match(/\*\*Question \d+:\*\* (.+?)\n\n/);
          const optionsMatch = match.match(/(\d+\. \*\*[^*]+\*\* - [^\n]+)/g);
          
          if (questionMatch && optionsMatch) {
            const question = questionMatch[1];
            const options = optionsMatch.map(opt => {
              const optMatch = opt.match(/\d+\. \*\*([^*]+)\*\* - (.+)/);
              return optMatch ? {
                label: optMatch[1],
                description: optMatch[2]
              } : { label: 'Unknown', description: '' };
            });
            
            questions.push({ question, options });
          }
        });
      }
    } catch (error) {
      console.error('Error parsing interactive questions:', error);
    }
    
    return questions;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 group"
        >
          <div className="relative">
            {/* Glow effect */}
            <div className="absolute inset-0 rounded-full bg-indigo-500/30 blur-xl animate-pulse"></div>
            
            {/* Button */}
            <div className="relative w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-[0_0_30px_rgba(99,102,241,0.5)] hover:shadow-[0_0_40px_rgba(99,102,241,0.7)] transition-all duration-300 hover:scale-110">
              <Sparkles className="w-6 h-6 text-white" />
              
              {/* Pulse ring */}
              <div className="absolute inset-0 rounded-full border-2 border-indigo-400 animate-ping opacity-75"></div>
            </div>
          </div>
        </button>
      )}

      {/* Assistant Popup */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[420px] h-[600px] flex flex-col bg-zinc-900/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-white/5 bg-zinc-900/50">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-500 border-2 border-zinc-900"></div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse"></div>
                  <span className="text-sm font-semibold text-indigo-300">CloudHelm Assistant</span>
                  {activeTasks.length > 0 && (
                    <button
                      onClick={() => setShowTaskPanel(!showTaskPanel)}
                      className="flex items-center gap-1 px-2 py-1 bg-indigo-500/20 hover:bg-indigo-500/30 rounded text-xs text-indigo-300 transition-colors"
                    >
                      <Users className="w-3 h-3" />
                      {activeTasks.length}
                    </button>
                  )}
                </div>
                <span className="text-[10px] text-zinc-500">v2.1 Model • Powered by Mistral AI</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-zinc-400" />
            </button>
          </div>

          {/* Repository Context */}
          {repositoryName && (
            <div className="px-4 py-2 bg-indigo-500/10 border-b border-indigo-500/20">
              <p className="text-xs text-indigo-300">
                <span className="font-medium">Analyzing:</span> {repositoryName}
              </p>
            </div>
          )}

          {/* Active Tasks Panel */}
          {showTaskPanel && activeTasks.length > 0 && (
            <div className="px-4 py-3 bg-zinc-800/30 border-b border-zinc-700/50">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-medium text-indigo-300">Active Subagents</span>
              </div>
              <div className="space-y-2">
                {activeTasks.map((task) => (
                  <div key={task.task_id} className="flex items-center justify-between p-2 bg-zinc-900/50 rounded border border-zinc-700/30">
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-white truncate">{task.description}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-zinc-400">{task.agent_type}</span>
                        <div className="flex items-center gap-1">
                          {task.status === 'running' ? (
                            <Clock className="w-3 h-3 text-yellow-400" />
                          ) : task.status === 'completed' ? (
                            <CheckCircle className="w-3 h-3 text-green-400" />
                          ) : (
                            <AlertCircle className="w-3 h-3 text-red-400" />
                          )}
                          <span className="text-xs text-zinc-500">{task.status}</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => checkTaskStatus(task.task_id)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 px-2 py-1 hover:bg-indigo-500/10 rounded transition-colors"
                    >
                      Check
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center px-6">
                <div className="w-16 h-16 rounded-full bg-indigo-500/10 flex items-center justify-center mb-4 border border-indigo-500/20">
                  <Sparkles className="w-8 h-8 text-indigo-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">CloudHelm Assistant</h3>
                <p className="text-sm text-zinc-400 mb-4">
                  I'm your AI coding companion! Ask me about code quality, testing strategies, architecture decisions, or anything development-related.
                </p>
                <div className="w-full space-y-2 text-left">
                  <button
                    onClick={() => setInput('How can I improve the testing strategy for this project?')}
                    className="w-full p-3 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs text-zinc-300 text-left transition-colors border border-zinc-700/50"
                  >
                    🧪 How can I improve testing in this project?
                  </button>
                  <button
                    onClick={() => setInput('What are potential security issues I should look for?')}
                    className="w-full p-3 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs text-zinc-300 text-left transition-colors border border-zinc-700/50"
                  >
                    🛡️ What security issues should I watch for?
                  </button>
                  <button
                    onClick={() => setInput('/task analyze the codebase structure and identify key components')}
                    className="w-full p-3 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs text-zinc-300 text-left transition-colors border border-zinc-700/50"
                  >
                    🤖 Delegate: Analyze codebase structure
                  </button>
                  <button
                    onClick={() => setInput('Can you review the code quality and suggest improvements?')}
                    className="w-full p-3 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs text-zinc-300 text-left transition-colors border border-zinc-700/50"
                  >
                    🔍 Review code quality and suggest improvements
                  </button>
                  <button
                    onClick={() => setInput('/agents')}
                    className="w-full p-3 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs text-zinc-300 text-left transition-colors border border-zinc-700/50"
                  >
                    👥 Show available subagents
                  </button>
                  <button
                    onClick={() => setInput('/help')}
                    className="w-full p-3 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs text-zinc-300 text-left transition-colors border border-zinc-700/50"
                  >
                    🤖 Show all capabilities
                  </button>
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center shrink-0 border border-indigo-500/30">
                    <Sparkles className="w-3 h-3 text-indigo-400" />
                  </div>
                )}
                
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-indigo-500/20 border border-indigo-500/30 text-white'
                      : 'bg-zinc-800/50 border border-zinc-700/50 text-zinc-300'
                  }`}
                >
                  <div className="text-sm leading-relaxed">
                    {renderMessageContent(message)}
                  </div>
                  <span className="text-[10px] text-zinc-500 mt-1 block">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>

                {message.role === 'user' && (
                  <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center shrink-0 border border-white/5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3 text-zinc-400">
                      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                      <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center shrink-0 border border-indigo-500/30">
                  <Sparkles className="w-3 h-3 text-indigo-400 animate-pulse" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="h-2 w-3/4 bg-zinc-800 rounded animate-pulse"></div>
                  <div className="h-2 w-1/2 bg-zinc-800 rounded animate-pulse"></div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/5 bg-zinc-900/50">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything, use /task to delegate work, or try /help for commands..."
                className="flex-1 px-4 py-2.5 bg-zinc-800/50 border border-zinc-700/50 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_25px_rgba(99,102,241,0.5)]"
              >
                <Send className="w-4 h-4 text-white" />
              </button>
            </div>
            <p className="text-[10px] text-zinc-600 mt-2 text-center">
              Powered by Mistral AI • Your conversational coding companion
            </p>
          </div>
        </div>
      )}
    </>
  );
}
