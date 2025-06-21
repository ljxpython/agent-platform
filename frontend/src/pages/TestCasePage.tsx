import React, { useState, useEffect, useRef } from 'react';
import {
  Button,
  Space,
  Typography,
  message as antMessage,
  Dropdown,
  Input,
  Progress,
  Tag,
} from 'antd';
import {
  ClearOutlined,
  SettingOutlined,
  RobotOutlined,
  MoreOutlined,
  BulbOutlined,
  CodeOutlined,
  EditOutlined,
  FileTextOutlined,
  HistoryOutlined,
  UploadOutlined,
  SendOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  CopyOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import { v4 as uuidv4 } from 'uuid';
import type { UploadFile } from 'antd';

import FileUpload from '@/components/FileUpload';
import PageLayout from '@/components/PageLayout';
import MarkdownRenderer from '@/components/MarkdownRenderer';

const { Title, Text } = Typography;
const { TextArea } = Input;

// 智能体消息数据接口
interface AgentMessageData {
  id: string;
  content: string;
  agentType: 'requirement_agent' | 'testcase_agent' | 'user_proxy';
  agentName: string;
  timestamp: string;
  roundNumber: number;
}

// SSE消息类型接口
interface SSEMessage {
  type?: string; // 消息类型: 'text_message', 'streaming_chunk', 'task_result', 'error'
  source?: string; // 消息来源: '需求分析智能体', '测试用例生成智能体'等
  content: string; // 消息内容
  conversation_id?: string; // 对话ID
  message_type?: string; // 业务类型: '用户需求', '文档解析结果', '需求分析', '测试用例生成'
  timestamp?: string; // 时间戳
  is_final?: boolean; // 是否最终消息
  is_complete?: boolean; // 是否完成（兼容性）
}

const TestCasePage: React.FC = () => {
  // 基础状态
  const [conversationId, setConversationId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [roundNumber, setRoundNumber] = useState(1);
  const [textContent, setTextContent] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<UploadFile[]>([]);
  const [userFeedback, setUserFeedback] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);

  // 流式输出状态
  const [currentAgent, setCurrentAgent] = useState<string>('');
  const [agentMessages, setAgentMessages] = useState<AgentMessageData[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [agentStreamingMap, setAgentStreamingMap] = useState<Record<string, string>>({});

  // 反馈状态
  const [waitingForFeedback, setWaitingForFeedback] = useState<boolean>(false);

  // 保存的测试用例内容（用于反馈后恢复）
  const [savedTestcaseContent, setSavedTestcaseContent] = useState<string>('');

  // 滚动控制状态
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [userScrolled, setUserScrolled] = useState<boolean>(false);
  const [lastScrollTop, setLastScrollTop] = useState<number>(0);

  // 引用
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const savedTestcaseContentRef = useRef<string>(''); // 使用ref保存测试用例内容

  const maxRounds = 3;

  // 滚动到底部
  const scrollToBottom = () => {
    if (autoScroll && !userScrolled && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // 强制滚动到底部（忽略用户滚动状态）
  const forceScrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // 重置滚动状态
  const resetScrollState = () => {
    console.log('🔄 重置滚动状态');
    setUserScrolled(false);
    setAutoScroll(true);
    setLastScrollTop(0);
  };

  // 检测用户是否手动滚动
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50; // 50px 容差

      // 检测用户是否主动向上滚动
      const isScrollingUp = scrollTop < lastScrollTop;
      setLastScrollTop(scrollTop);

      // 如果用户主动向上滚动，禁用自动滚动
      if (isScrollingUp && !userScrolled) {
        console.log('🔒 用户向上滚动，禁用自动滚动');
        setUserScrolled(true);
        setAutoScroll(false);
      }
      // 如果用户滚动到底部，重新启用自动滚动
      else if (isAtBottom && userScrolled) {
        console.log('🔓 用户滚动到底部，启用自动滚动');
        setUserScrolled(false);
        setAutoScroll(true);
      }
    }
  };

  // 智能滚动控制 - 只在特定条件下自动滚动
  useEffect(() => {
    // 只有在以下情况下才自动滚动：
    // 1. 有流式输出正在进行 (currentAgent 存在)
    // 2. 自动滚动开启
    // 3. 用户没有手动滚动
    if (currentAgent && autoScroll && !userScrolled) {
      // 使用 setTimeout 避免频繁滚动
      const scrollTimer = setTimeout(() => {
        scrollToBottom();
      }, 100);

      return () => clearTimeout(scrollTimer);
    }
  }, [agentMessages.length, currentAgent, autoScroll, userScrolled]); // 只监听消息数量变化，而不是整个消息数组

  // 初始化对话ID
  useEffect(() => {
    if (!conversationId) {
      setConversationId(uuidv4());
    }
  }, []);

  // 清理 EventSource
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 处理错误
  useEffect(() => {
    if (streamError) {
      antMessage.error(`生成失败: ${streamError}`);
      setAnalysisProgress(0);
    }
  }, [streamError]);

  // 文件变化处理
  const handleFilesChange = (files: UploadFile[]) => {
    setSelectedFiles(files);
    if (files.length > 0 && currentStep === 0) {
      setCurrentStep(0);
    }
  };

  // 获取智能体显示名称
  const getAgentDisplayName = (agentType: string, agentName: string): string => {
    if (agentName.includes('需求分析') || agentType === 'requirement_agent') {
      return '需求分析师';
    } else if (agentName.includes('测试用例') || agentName.includes('优化') || agentName.includes('结构化') || agentType === 'testcase_agent') {
      return '测试用例专家';
    } else if (agentName.includes('用户') || agentType === 'user_proxy') {
      return '用户代理';
    } else {
      return '智能助手';
    }
  };

  // 获取智能体颜色配置
  const getAgentColor = (agentType: string): string => {
    switch (agentType) {
      case 'requirement_agent':
        return '#722ed1';
      case 'testcase_agent':
        return '#52c41a';
      case 'user_proxy':
        return '#1890ff';
      default:
        return '#8c8c8c';
    }
  };

  const getAgentBackground = (agentType: string): string => {
    switch (agentType) {
      case 'requirement_agent':
        return '#f9f0ff';
      case 'testcase_agent':
        return '#f6ffed';
      case 'user_proxy':
        return '#e6f7ff';
      default:
        return '#f5f5f5';
    }
  };

  const getAgentBorderColor = (agentType: string): string => {
    switch (agentType) {
      case 'requirement_agent':
        return '#d3adf7';
      case 'testcase_agent':
        return '#b7eb8f';
      case 'user_proxy':
        return '#91d5ff';
      default:
        return '#d9d9d9';
    }
  };

  const getAgentTagColor = (agentType: string): string => {
    switch (agentType) {
      case 'requirement_agent':
        return 'purple';
      case 'testcase_agent':
        return 'green';
      case 'user_proxy':
        return 'blue';
      default:
        return 'default';
    }
  };

  // 处理文件上传
  const handleFileUpload = async (file: File): Promise<boolean> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('conversation_id', conversationId);

      const response = await fetch('/api/v1/testcase/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`文件上传失败: ${response.status}`);
      }

      const result = await response.json();
      console.log('文件上传成功:', result);
      antMessage.success(`文件 ${file.name} 上传成功`);
      return true;
    } catch (error: any) {
      console.error('文件上传失败:', error);
      antMessage.error(`文件上传失败: ${error.message}`);
      return false;
    }
  };

  // 处理多个文件上传
  const handleMultipleFileUpload = async (): Promise<boolean> => {
    if (selectedFiles.length === 0) return true;

    try {
      const uploadPromises = selectedFiles.map(async (file) => {
        if (file.originFileObj) {
          return await handleFileUpload(file.originFileObj);
        }
        return false;
      });

      const results = await Promise.all(uploadPromises);
      const successCount = results.filter(Boolean).length;

      if (successCount === selectedFiles.length) {
        antMessage.success(`成功上传 ${successCount} 个文件`);
        return true;
      } else {
        antMessage.warning(`上传完成，成功 ${successCount}/${selectedFiles.length} 个文件`);
        return successCount > 0;
      }
    } catch (error: any) {
      console.error('批量文件上传失败:', error);
      antMessage.error('批量文件上传失败');
      return false;
    }
  };

  // SSE处理函数
  const processSSEStream = async (reader: ReadableStreamDefaultReader<Uint8Array>) => {
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('✅ SSE流处理完成');
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: SSEMessage = JSON.parse(line.slice(6));
            console.log('📤 收到SSE消息:', {
              type: data.type,
              message_type: data.message_type,
              source: data.source,
              content_length: data.content?.length
            });

            // 更新conversation_id（如果还没有设置）
            if (data.conversation_id && !conversationId) {
              setConversationId(data.conversation_id);
            }

            // 简化的消息处理逻辑
            if (data.type === 'text_message') {
              // 用户模块消息
              if (data.message_type === '用户需求' || data.message_type === '文档解析结果') {
                const userMessage: AgentMessageData = {
                  id: `user_${Date.now()}_${Math.random()}`,
                  content: `## 📋 ${data.message_type}\n\n${data.content || ''}`,
                  agentType: 'user_proxy',
                  agentName: '用户模块',
                  timestamp: data.timestamp || new Date().toISOString(),
                  roundNumber: roundNumber
                };
                setAgentMessages(prev => [...prev, userMessage]);
                setAnalysisProgress(data.message_type === '用户需求' ? 20 : 30);

              } else if (data.message_type === '需求分析') {
                // 需求分析智能体的完整输出
                console.log('🧠 需求分析完成，显示最终结果');
                const agentStreamContent = agentStreamingMap[data.source || ''] || '';
                const finalContent = agentStreamContent.trim() || data.content || '';

                const analysisMessage: AgentMessageData = {
                  id: `requirement_final_${roundNumber}`,
                  content: finalContent,
                  agentType: 'requirement_agent',
                  agentName: '需求分析师',
                  timestamp: data.timestamp || new Date().toISOString(),
                  roundNumber: roundNumber
                };

                setAgentMessages(prev => {
                  // 移除流式消息，添加最终消息
                  const filtered = prev.filter(msg => msg.id !== `requirement_streaming_${roundNumber}`);
                  return [...filtered, analysisMessage];
                });

                // 清理该智能体的流式内容
                setAgentStreamingMap(prev => {
                  const updated = { ...prev };
                  delete updated[data.source || ''];
                  return updated;
                });

                if (currentAgent === '需求分析师') {
                  setCurrentAgent('');
                }
                setAnalysisProgress(70);

              } else if (data.message_type === '测试用例生成' || data.message_type === '测试用例优化') {
                // 测试用例生成/优化智能体的完整输出
                console.log('🎯 测试用例处理完成，显示最终结果');
                console.log('📊 当前轮次:', roundNumber, '数据来源:', data.source);
                console.log('📊 agentStreamingMap:', agentStreamingMap);
                console.log('📊 当前所有消息:', agentMessages.map(msg => ({
                  id: msg.id,
                  agentType: msg.agentType,
                  roundNumber: msg.roundNumber,
                  contentLength: msg.content.length
                })));

                // 获取流式内容，优先使用保存的内容
                let agentStreamContent = agentStreamingMap[data.source || ''] || '';
                console.log('📊 从agentStreamingMap获取的内容长度:', agentStreamContent.length);
                console.log('📊 保存的测试用例内容长度:', savedTestcaseContent.length);
                console.log('📊 保存的测试用例内容预览:', savedTestcaseContent.substring(0, 100) + '...');

                // 如果当前轮次没有流式内容，优先使用ref中保存的内容
                if (!agentStreamContent && savedTestcaseContentRef.current) {
                  agentStreamContent = savedTestcaseContentRef.current;
                  console.log('💾 使用ref中保存的测试用例内容，长度:', agentStreamContent.length);
                } else if (!agentStreamContent && savedTestcaseContent) {
                  agentStreamContent = savedTestcaseContent;
                  console.log('💾 使用state中保存的测试用例内容，长度:', agentStreamContent.length);
                }

                // 如果还是没有内容，尝试查找现有消息
                if (!agentStreamContent) {
                  console.log('🔍 agentStreamingMap中没有内容，查找现有消息...');

                  // 查找现有消息中最新的测试用例内容（包括流式消息）
                  const testcaseMessages = agentMessages
                    .filter(msg => msg.agentType === 'testcase_agent')
                    .sort((a, b) => b.roundNumber - a.roundNumber);

                  console.log('📋 找到的测试用例消息:', testcaseMessages.map(msg => ({
                    id: msg.id,
                    roundNumber: msg.roundNumber,
                    contentLength: msg.content.length,
                    contentPreview: msg.content.substring(0, 100) + '...'
                  })));

                  if (testcaseMessages.length > 0) {
                    agentStreamContent = testcaseMessages[0].content;
                    console.log('📋 使用现有测试用例内容，长度:', agentStreamContent.length);
                  }
                }

                // 如果还是没有内容，尝试从所有智能体的流式内容中查找
                if (!agentStreamContent) {
                  console.log('🔍 仍然没有内容，检查所有agentStreamingMap条目...');
                  Object.keys(agentStreamingMap).forEach(key => {
                    console.log(`📊 agentStreamingMap[${key}]:`, agentStreamingMap[key].length, '字符');
                    if (agentStreamingMap[key] && agentStreamingMap[key].length > 100) {
                      agentStreamContent = agentStreamingMap[key];
                      console.log('📋 使用agentStreamingMap中的内容:', key, '长度:', agentStreamContent.length);
                    }
                  });
                }

                // 优先使用流式内容，如果没有则使用data.content，但要避免使用用户反馈内容
                let finalContent = agentStreamContent.trim();
                if (!finalContent && data.content && data.content !== '同意' && data.content !== '不同意') {
                  finalContent = data.content;
                  console.log('📋 使用data.content作为最终内容，长度:', finalContent.length);
                }

                console.log('📝 最终内容长度:', finalContent.length);
                console.log('📝 最终内容预览:', finalContent.substring(0, 200) + '...');

                const testcaseMessage: AgentMessageData = {
                  id: `testcase_final_${roundNumber}`,
                  content: finalContent,
                  agentType: 'testcase_agent',
                  agentName: '测试用例专家',
                  timestamp: data.timestamp || new Date().toISOString(),
                  roundNumber: roundNumber
                };

                setAgentMessages(prev => {
                  // 移除当前轮次和之前轮次的流式消息，添加最终消息
                  const filtered = prev.filter(msg =>
                    !msg.id.startsWith('testcase_streaming_') &&
                    !msg.id.startsWith('testcase_final_')
                  );
                  return [...filtered, testcaseMessage];
                });

                // 保留流式内容，不要删除，以备反馈后使用
                // setAgentStreamingMap(prev => {
                //   const updated = { ...prev };
                //   delete updated[data.source || ''];
                //   return updated;
                // });
                console.log('📋 保留agentStreamingMap中的内容以备后续使用');

                if (currentAgent === '测试用例专家') {
                  setCurrentAgent('');
                }

                // 标记完成
                setIsComplete(true);
                setCurrentStep(2);
                setAnalysisProgress(100);
                const messageType = data.message_type === '测试用例优化' ? '测试用例优化完成！' : '测试用例生成完成！';
                antMessage.success(messageType);
              }

            } else if (data.type === 'user_input_request') {
              // 处理用户反馈请求
              console.log('💬 收到用户反馈请求:', data.content);

              // 在进入反馈阶段前，确保测试用例内容已保存
              console.log('🔍 检查agentStreamingMap:', agentStreamingMap);
              console.log('🔍 agentStreamingMap的所有值:', Object.values(agentStreamingMap));
              console.log('🔍 ref中保存的内容长度:', savedTestcaseContentRef.current.length);
              console.log('🔍 state中保存的内容长度:', savedTestcaseContent.length);

              // 如果ref中没有内容，尝试从其他地方获取
              if (!savedTestcaseContentRef.current) {
                const currentTestcaseContent = Object.values(agentStreamingMap).find(content => content.length > 100) || '';
                console.log('🔍 从agentStreamingMap找到的测试用例内容长度:', currentTestcaseContent.length);

                if (currentTestcaseContent) {
                  setSavedTestcaseContent(currentTestcaseContent);
                  savedTestcaseContentRef.current = currentTestcaseContent;
                  console.log('💾 保存测试用例内容，长度:', currentTestcaseContent.length);
                } else {
                  console.log('⚠️ 没有找到可保存的测试用例内容');
                  // 尝试从当前消息中查找
                  const testcaseMsg = agentMessages.find(msg => msg.agentType === 'testcase_agent' && msg.content.length > 100);
                  if (testcaseMsg) {
                    setSavedTestcaseContent(testcaseMsg.content);
                    savedTestcaseContentRef.current = testcaseMsg.content;
                    console.log('💾 从消息中保存测试用例内容，长度:', testcaseMsg.content.length);
                  }
                }
              } else {
                console.log('✅ ref中已有保存的测试用例内容，长度:', savedTestcaseContentRef.current.length);
              }

              const feedbackRequestMessage: AgentMessageData = {
                id: `feedback_request_${Date.now()}_${Math.random()}`,
                content: `## 💬 用户反馈请求\n\n${data.content || ''}`,
                agentType: 'testcase_agent',
                agentName: '测试用例专家',
                timestamp: data.timestamp || new Date().toISOString(),
                roundNumber: roundNumber
              };

              // 只添加新消息，不覆盖已有消息
              setAgentMessages(prev => [...prev, feedbackRequestMessage]);

              // 进入反馈阶段，重置loading状态以允许用户输入
              setCurrentStep(2);
              setLoading(false); // 重要：重置loading状态
              setCurrentAgent(''); // 清空当前智能体状态
              setWaitingForFeedback(true); // 标记正在等待用户反馈
              setIsComplete(false); // 保持未完成状态，以显示反馈区域
              antMessage.info('请查看生成的测试用例并提供反馈');

            } else if (data.type === 'streaming_chunk') {
              // 处理流式输出块
              console.log('🔥 处理streaming_chunk:', data.source, '内容:', data.content);

              // 更新当前智能体的流式内容（累积）
              setAgentStreamingMap(prev => {
                const newContent = (prev[data.source || ''] || '') + (data.content || '');
                const updatedMap = {...prev, [data.source || '']: newContent};

                // 根据智能体来源创建或更新流式消息
                if (data.source === '需求分析智能体') {
                  setCurrentAgent('需求分析师');
                  setAnalysisProgress(60);

                  setAgentMessages(prevMessages => {
                    const streamingMessage: AgentMessageData = {
                      id: `requirement_streaming_${roundNumber}`,
                      content: newContent,  // 使用累积内容
                      agentType: 'requirement_agent',
                      agentName: '需求分析师',
                      timestamp: data.timestamp || new Date().toISOString(),
                      roundNumber: roundNumber
                    };

                    const existingIndex = prevMessages.findIndex(msg =>
                      msg.id === `requirement_streaming_${roundNumber}`
                    );

                    if (existingIndex >= 0) {
                      const updated = [...prevMessages];
                      updated[existingIndex] = streamingMessage;
                      return updated;
                    } else {
                      return [...prevMessages, streamingMessage];
                    }
                  });

                } else if (data.source === '测试用例生成智能体' || data.source === '测试用例优化智能体') {
                  setCurrentAgent('测试用例专家');
                  setAnalysisProgress(80);

                  setAgentMessages(prevMessages => {
                    const streamingMessage: AgentMessageData = {
                      id: `testcase_streaming_${roundNumber}`,
                      content: newContent,  // 使用累积内容
                      agentType: 'testcase_agent',
                      agentName: '测试用例专家',
                      timestamp: data.timestamp || new Date().toISOString(),
                      roundNumber: roundNumber
                    };

                    console.log('🎯 当前测试用例专家流式内容长度:', newContent.length);

                    // 实时保存测试用例内容
                    if (newContent.length > 100) {
                      setSavedTestcaseContent(newContent);
                      savedTestcaseContentRef.current = newContent; // 同时保存到ref
                      console.log('💾 实时保存测试用例内容，长度:', newContent.length);
                    }

                    const existingIndex = prevMessages.findIndex(msg =>
                      msg.id === `testcase_streaming_${roundNumber}`
                    );

                    if (existingIndex >= 0) {
                      const updated = [...prevMessages];
                      updated[existingIndex] = streamingMessage;
                      return updated;
                    } else {
                      return [...prevMessages, streamingMessage];
                    }
                  });
                }

                return updatedMap;
              });

            } else if (data.type === 'task_result') {
              // 任务完成
              console.log('🏁 任务完成');
              setIsComplete(true);
              setCurrentStep(2);
              setAnalysisProgress(100);
              antMessage.success('测试用例生成完成！');
              break;

            } else if (data.type === 'error') {
              // 错误处理
              console.error('❌ 收到错误消息:', data.content);
              setStreamError(data.content || '未知错误');
              antMessage.error('生成过程中出现错误');
              break;
            }

          } catch (e) {
            console.error('❌ 解析SSE数据失败:', e, '原始行:', line);
          }
        }
      }
    }
  };

  // 生成测试用例
  const generateTestCase = async () => {
    if (!textContent.trim() && selectedFiles.length === 0) {
      antMessage.warning('请输入文本内容或上传文件');
      return;
    }

    // 检查文件是否都已成功选择
    const hasUploadingFiles = selectedFiles.some(file => file.status === 'uploading');
    const hasFailedFiles = selectedFiles.some(file => file.status === 'error');

    if (hasUploadingFiles) {
      antMessage.warning('请等待文件处理完成');
      return;
    }

    if (hasFailedFiles) {
      antMessage.error('存在处理失败的文件，请重新选择');
      return;
    }

    setLoading(true);
    setCurrentStep(1);
    setAnalysisProgress(0);
    setStreamError(null);
    setCurrentAgent('');
    setAgentMessages([]);
    setAgentStreamingMap({});
    setIsComplete(false);
    setWaitingForFeedback(false); // 重置等待反馈状态
    setSavedTestcaseContent(''); // 清空保存的测试用例内容
    savedTestcaseContentRef.current = ''; // 清空ref中的内容

    // 重置滚动状态
    resetScrollState();

    console.log('🚀 开始测试用例生成流程，重置所有状态');
    console.log('📊 初始状态 - currentAgent:', '', 'agentMessages:', []);

    try {
      // 步骤1: 先上传文件（如果有文件需要上传）
      if (selectedFiles.length > 0) {
        console.log('📁 开始上传文件:', selectedFiles.length, '个');
        const uploadSuccess = await handleMultipleFileUpload();
        if (!uploadSuccess) {
          throw new Error('文件上传失败');
        }
        setAnalysisProgress(30);
      }

      // 步骤2: 构建生成请求数据
      let currentConversationId = conversationId;
      if (!currentConversationId) {
        currentConversationId = uuidv4();
        console.log('🆕 生成新的conversation_id:', currentConversationId);
        setConversationId(currentConversationId);
      }

      const requestData = {
        conversation_id: currentConversationId,
        text_content: textContent.trim() || "",
        round_number: roundNumber,
        enable_streaming: true
      };

      setAnalysisProgress(40);
      console.log('🚀 开始生成测试用例:', requestData);

      // 发送请求
      const response = await fetch('/api/v1/testcase/generate/streaming', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法获取响应流');
      }

      // 处理SSE流
      await processSSEStream(reader);

    } catch (error: any) {
      console.error('生成测试用例失败:', error);
      antMessage.error(`生成测试用例失败: ${error.message || '请重试'}`);
      setCurrentStep(0);
      setAnalysisProgress(0);
      setStreamError(error.message || '网络请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 提交反馈
  const submitFeedback = async () => {
    if (!userFeedback.trim()) {
      antMessage.warning('请输入反馈内容');
      return;
    }

    if (roundNumber >= maxRounds) {
      antMessage.warning('已达到最大交互轮次');
      return;
    }

    if (!conversationId) {
      antMessage.error('没有有效的对话ID');
      return;
    }

    setLoading(true);
    setStreamError(null);
    setWaitingForFeedback(false); // 重置等待反馈状态
    // 不清空 currentAgent 和 agentStreamingMap，保留已有的测试用例内容

    // 重置滚动状态，确保用户能看到新的反馈处理过程
    resetScrollState();

    try {
      console.log('🔄 提交反馈:', userFeedback.trim());
      console.log('🔍 提交反馈时保存的测试用例内容长度:', savedTestcaseContent.length);

      // 添加用户反馈消息到消息列表
      const feedbackMessage: AgentMessageData = {
        id: `user_feedback_${Date.now()}_${Math.random()}`,
        content: `## 💬 用户反馈\n\n${userFeedback.trim()}`,
        agentType: 'user_proxy',
        agentName: '用户代理',
        timestamp: new Date().toISOString(),
        roundNumber: roundNumber
      };

      setAgentMessages(prev => [...prev, feedbackMessage]);

      // 提交反馈到简单接口
      const feedbackResponse = await fetch(`/api/v1/testcase/feedback?conversation_id=${encodeURIComponent(conversationId)}&message=${encodeURIComponent(userFeedback.trim())}`, {
        method: 'GET',
      });

      if (!feedbackResponse.ok) {
        throw new Error(`反馈提交失败: ${feedbackResponse.status}`);
      }

      // 清空用户反馈输入，但先保存当前轮次用于后续请求
      const currentRound = roundNumber;
      setUserFeedback('');
      setRoundNumber(prev => prev + 1);
      antMessage.success('反馈提交成功，正在处理...');

      // 启动一个新的流式连接来监听智能体的反馈响应
      // 使用特殊标记表示这是反馈后的监听请求
      const streamingData = {
        conversation_id: conversationId,
        text_content: "FEEDBACK_LISTENING", // 特殊标记，表示这是反馈后的流式监听
        round_number: currentRound + 1, // 使用新的轮次
        enable_streaming: true
      };

      const streamingResponse = await fetch('/api/v1/testcase/generate/streaming', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(streamingData),
      });

      if (!streamingResponse.ok) {
        throw new Error(`流式监听失败: ${streamingResponse.status}`);
      }

      const reader = streamingResponse.body?.getReader();
      if (!reader) {
        throw new Error('无法获取流式响应');
      }

      // 处理流式响应
      await processSSEStream(reader);

    } catch (error: any) {
      console.error('提交反馈失败:', error);
      antMessage.error(`提交反馈失败: ${error.message || '请重试'}`);
      setStreamError(error.message || '反馈提交失败');
    } finally {
      setLoading(false);
    }
  };

  // 停止生成
  const stopGeneration = () => {
    setLoading(false);
    setCurrentStep(0);
    setAnalysisProgress(0);
    setCurrentAgent('');
    setAgentStreamingMap({});
    antMessage.info('已停止生成');
  };

  // 重置对话
  const resetConversation = async () => {
    console.log('🔄 开始重置对话');

    // 如果有现有的conversation_id，先清除后端历史记录
    if (conversationId) {
      try {
        console.log('🗑️ 清除后端历史记录:', conversationId);
        const response = await fetch(`/api/v1/testcase/conversation/${conversationId}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          console.log('✅ 后端历史记录清除成功');
        } else {
          console.warn('⚠️ 后端历史记录清除失败，但继续重置前端状态');
        }
      } catch (error) {
        console.warn('⚠️ 清除后端历史记录时出错:', error);
      }
    }

    // 生成新的conversation_id
    const newConversationId = uuidv4();
    console.log('🆕 生成新的conversation_id:', newConversationId);

    // 重置所有状态
    setAgentMessages([]);
    setConversationId(newConversationId);
    setRoundNumber(1);
    setCurrentStep(0);
    setTextContent('');
    setSelectedFiles([]);
    setUserFeedback('');
    setIsComplete(false);
    setAnalysisProgress(0);
    setCurrentAgent('');
    setAgentStreamingMap({});
    setLoading(false);
    setStreamError(null);
    setWaitingForFeedback(false); // 重置等待反馈状态
    setSavedTestcaseContent(''); // 清空保存的测试用例内容
    savedTestcaseContentRef.current = ''; // 清空ref中的内容

    // 重置滚动状态
    resetScrollState();

    antMessage.success('已重新开始，生成新的对话');
    console.log('🎉 对话重置完成，新conversation_id:', newConversationId);
  };

  // 测试用例生成相关的建议卡片
  const suggestionCards = [
    {
      icon: <FileTextOutlined />,
      title: "需求文档分析",
      description: "上传需求文档，AI智能分析功能点和业务逻辑",
      color: "#f59e0b"
    },
    {
      icon: <CodeOutlined />,
      title: "测试用例生成",
      description: "基于需求自动生成完整的测试用例，包含测试步骤和预期结果",
      color: "#10b981"
    },
    {
      icon: <BulbOutlined />,
      title: "用例优化建议",
      description: "根据反馈优化测试用例，提高测试覆盖率和有效性",
      color: "#8b5cf6"
    },
    {
      icon: <EditOutlined />,
      title: "交互式改进",
      description: "支持多轮对话，根据您的反馈持续改进测试用例质量",
      color: "#ef4444"
    }
  ];

  const menuItems = [
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: '对话历史',
    },
    {
      key: 'clear',
      icon: <ClearOutlined />,
      label: '清除对话',
      onClick: resetConversation,
      disabled: agentMessages.length === 0 && !loading
    },
    {
      key: 'export',
      icon: <DownloadOutlined />,
      label: '导出结果',
      disabled: agentMessages.length === 0
    },
    {
      key: 'copy',
      icon: <CopyOutlined />,
      label: '复制结果',
      disabled: agentMessages.length === 0
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置'
    }
  ];

  return (
    <PageLayout background="#f5f5f5" padding="0">
      <style>
        {`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
          .glass-effect {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
          }
          .gemini-hover {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .gemini-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
          }
        `}
      </style>
      <div style={{ minHeight: 'calc(100vh - 64px)', position: 'relative', background: 'transparent' }}>
        <div style={{
          height: 'calc(100vh - 64px)',
          display: 'flex',
          flexDirection: 'column',
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '20px',
          position: 'relative',
          zIndex: 1
        }}>
          {/* Gemini 风格头部 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '20px 0',
            borderBottom: agentMessages.length > 0 || loading ? '1px solid #e8e8e8' : 'none'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 18,
                fontWeight: 'bold'
              }}>
                T
              </div>
              <div>
                <Title level={3} style={{ margin: 0, color: '#262626', fontWeight: 500 }}>
                  测试用例专家
                </Title>
                <Text style={{ color: '#8c8c8c', fontSize: 14 }}>
                  智能分析需求文档，自动生成专业测试用例
                </Text>
              </div>
            </div>

            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button
                type="text"
                icon={<MoreOutlined />}
                style={{
                  color: '#595959',
                  border: '1px solid #d9d9d9',
                  borderRadius: 20
                }}
                className="gemini-hover"
              />
            </Dropdown>
          </div>

          {/* 主要内容区域 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', paddingTop: 20 }}>
            {agentMessages.length === 0 && !loading && !currentAgent ? (
              /* 欢迎页面 - Gemini 风格 */
              <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                padding: '40px 20px'
              }}>
                <div style={{
                  marginBottom: 48,
                  animation: 'geminiSlideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
                }}>
                  <Title level={1} style={{
                    color: '#262626',
                    fontSize: 48,
                    fontWeight: 300,
                    marginBottom: 16,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    你好，我是测试用例专家
                  </Title>
                  <Text style={{
                    color: '#595959',
                    fontSize: 18,
                    display: 'block',
                    marginBottom: 8
                  }}>
                    我可以帮助您分析需求文档，生成专业的测试用例
                  </Text>
                  <Text style={{
                    color: '#8c8c8c',
                    fontSize: 14
                  }}>
                    上传需求文档或描述您的测试需求，开始智能分析
                  </Text>
                </div>

                {/* 建议卡片 */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: 16,
                  width: '100%',
                  maxWidth: 800,
                  marginBottom: 40
                }}>
                  {suggestionCards.map((card, index) => (
                    <div
                      key={index}
                      className="glass-effect gemini-hover"
                      style={{
                        padding: 20,
                        borderRadius: 16,
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        animationDelay: `${index * 0.1}s`
                      }}
                      onClick={() => setTextContent(card.description)}
                    >
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: 12
                      }}>
                        <div style={{
                          width: 32,
                          height: 32,
                          borderRadius: 8,
                          backgroundColor: card.color,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          marginRight: 12
                        }}>
                          {card.icon}
                        </div>
                        <Text style={{
                          color: '#262626',
                          fontWeight: 500,
                          fontSize: 16
                        }}>
                          {card.title}
                        </Text>
                      </div>
                      <Text style={{
                        color: '#595959',
                        fontSize: 14,
                        lineHeight: 1.5
                      }}>
                        {card.description}
                      </Text>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* 工作模式 - 单栏布局 */
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {/* 操作区域 */}
                <div style={{
                  background: 'white',
                  borderRadius: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  marginBottom: 20
                }}>
                  {/* 输入区域 - 从上到下排列 */}
                  <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: 20 }}>

                    {/* 第一步：导入需求文档 */}
                    <div style={{
                      background: currentStep >= 0 ? '#f6ffed' : '#fafafa',
                      border: `1px solid ${currentStep >= 0 ? '#b7eb8f' : '#d9d9d9'}`,
                      borderRadius: 12,
                      padding: 20,
                      transition: 'all 0.3s ease'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: 16,
                        color: currentStep >= 0 ? '#52c41a' : '#8c8c8c'
                      }}>
                        <div style={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          background: currentStep >= 0 ? '#52c41a' : '#d9d9d9',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 14,
                          fontWeight: 'bold',
                          marginRight: 12
                        }}>
                          1
                        </div>
                        <UploadOutlined style={{ marginRight: 8, fontSize: 16 }} />
                        <Text strong style={{ color: 'inherit', fontSize: 16 }}>导入需求文档</Text>
                      </div>

                      <div style={{ marginLeft: 44, marginBottom: 12 }}>
                        <FileUpload onFilesChange={handleFilesChange} />
                      </div>

                      <div style={{ marginLeft: 44, fontSize: 12, color: '#8c8c8c' }}>
                        支持格式：PDF、Word、Excel、TXT等，最大5个文件
                      </div>
                    </div>

                    {/* 第二步：输入分析重点 + AI智能分析 */}
                    <div style={{
                      background: currentStep >= 1 ? '#f6ffed' : '#fafafa',
                      border: `1px solid ${currentStep >= 1 ? '#b7eb8f' : '#d9d9d9'}`,
                      borderRadius: 12,
                      padding: 20,
                      transition: 'all 0.3s ease'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: 16,
                        color: currentStep >= 1 ? '#52c41a' : '#8c8c8c'
                      }}>
                        <div style={{
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          background: currentStep >= 1 ? '#52c41a' : '#d9d9d9',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 14,
                          fontWeight: 'bold',
                          marginRight: 12
                        }}>
                          2
                        </div>
                        <EditOutlined style={{ marginRight: 8, fontSize: 16 }} />
                        <Text strong style={{ color: 'inherit', fontSize: 16 }}>输入分析重点</Text>
                      </div>

                      <div style={{ marginLeft: 44 }}>
                        <TextArea
                          value={textContent}
                          onChange={(e) => setTextContent(e.target.value)}
                          placeholder="请描述您希望重点关注的测试内容、功能要求、性能要求等..."
                          rows={4}
                          disabled={loading}
                          style={{
                            borderRadius: 8,
                            resize: 'none',
                            marginBottom: 16
                          }}
                        />

                        {/* AI智能分析按钮和进度 */}
                        {loading && (
                          <div style={{ marginBottom: 16 }}>
                            <Progress
                              percent={analysisProgress}
                              size="small"
                              status="active"
                              strokeColor={{
                                '0%': '#667eea',
                                '100%': '#764ba2',
                              }}
                            />
                            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 8 }}>
                              正在分析需求文档，生成测试用例...
                            </div>
                          </div>
                        )}

                        {!loading ? (
                          <Button
                            type="primary"
                            icon={<BulbOutlined />}
                            onClick={generateTestCase}
                            loading={loading}
                            size="large"
                            disabled={!textContent.trim() && selectedFiles.length === 0}
                            style={{
                              width: '100%',
                              height: 48,
                              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                              border: 'none',
                              borderRadius: 8,
                              fontSize: 16,
                              fontWeight: 600
                            }}
                          >
                            开始AI智能分析
                          </Button>
                        ) : (
                          <Button
                            danger
                            icon={<ReloadOutlined />}
                            onClick={stopGeneration}
                            size="large"
                            style={{
                              width: '100%',
                              height: 48,
                              fontSize: 16,
                              fontWeight: 600,
                              borderRadius: 8
                            }}
                          >
                            停止生成
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI分析结果区域 - 移到下面 */}
                {(agentMessages.length > 0 || currentAgent || loading) && (
                  <div style={{
                    background: 'white',
                    borderRadius: '20px',
                    padding: '24px',
                    marginTop: 20
                  }}>
                    {/* 标题栏 */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: 24,
                      paddingBottom: 16,
                      borderBottom: '1px solid #f0f0f0'
                    }}>
                      <div>
                        <Title level={4} style={{ margin: 0, color: '#262626' }}>
                          AI分析结果
                        </Title>
                        <Text type="secondary">根据需求内容生成的测试用例</Text>
                      </div>

                      {agentMessages.length > 0 && (
                        <Space>
                          {/* 滚动控制按钮 */}
                          {userScrolled && (
                            <Button
                              icon={<ArrowDownOutlined />}
                              type="text"
                              size="small"
                              onClick={() => {
                                console.log('🔄 用户点击回到底部');
                                setUserScrolled(false);
                                setAutoScroll(true);
                                forceScrollToBottom();
                              }}
                              style={{
                                color: '#1890ff',
                                border: '1px solid #1890ff',
                                animation: currentAgent ? 'pulse 2s infinite' : 'none'
                              }}
                              title={currentAgent ? '有新内容正在生成，点击回到底部查看' : '回到底部'}
                            >
                              回到底部 {currentAgent && '🔴'}
                            </Button>
                          )}
                          <Button icon={<DownloadOutlined />} type="text">
                            导出
                          </Button>
                          <Button icon={<CopyOutlined />} type="text">
                            复制
                          </Button>
                        </Space>
                      )}
                    </div>

                    {/* 内容区域 */}
                    <div
                      ref={scrollContainerRef}
                      onScroll={handleScroll}
                      style={{
                        maxHeight: '60vh',
                        overflowY: 'auto',
                        paddingRight: 8
                      }}
                    >
                      {/* AI生成的消息列表 - 显示所有消息 */}
                      <div style={{ marginBottom: 24 }}>
                        {agentMessages
                          .filter(msg =>
                            msg.agentType === 'user_proxy' ||
                            msg.agentType === 'requirement_agent' ||
                            msg.agentType === 'testcase_agent'
                          )
                          .map((msg) => {
                            // 判断是否为流式消息
                            const isStreaming = msg.id.includes('_streaming_') &&
                              (msg.id.startsWith('requirement_streaming_') || msg.id.startsWith('testcase_streaming_'));

                            // 判断是否为反馈请求消息
                            const isFeedbackRequest = msg.id.includes('feedback_request');

                            return (
                              <div key={msg.id} style={{ marginBottom: 24 }}>
                                <div style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  marginBottom: 12,
                                  padding: '8px 12px',
                                  background: getAgentBackground(msg.agentType),
                                  borderRadius: 6,
                                  border: `1px solid ${getAgentBorderColor(msg.agentType)}`
                                }}>
                                  <RobotOutlined style={{
                                    color: getAgentColor(msg.agentType),
                                    marginRight: 8
                                  }} />
                                  <Text strong style={{
                                    color: getAgentColor(msg.agentType)
                                  }}>
                                    {getAgentDisplayName(msg.agentType, msg.agentName)}
                                  </Text>
                                  {isStreaming ? (
                                    <Tag color="processing" style={{ marginLeft: 'auto' }}>
                                      正在输出...
                                    </Tag>
                                  ) : isFeedbackRequest ? (
                                    <Tag color="orange" style={{ marginLeft: 'auto' }}>
                                      等待反馈
                                    </Tag>
                                  ) : (
                                    <Tag
                                      color={getAgentTagColor(msg.agentType)}
                                      style={{ marginLeft: 'auto' }}
                                    >
                                      第 {msg.roundNumber} 轮
                                    </Tag>
                                  )}
                                </div>

                                <div style={{
                                  padding: 16,
                                  background: '#f8f9fa',
                                  borderRadius: 8,
                                  border: '1px solid #f0f0f0',
                                  lineHeight: 1.6,
                                  minHeight: 60
                                }}>
                                  <MarkdownRenderer content={msg.content} />
                                  {isStreaming && (
                                    <div style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      marginTop: 8
                                    }}>
                                      <span style={{
                                        display: 'inline-block',
                                        width: 8,
                                        height: 16,
                                        background: getAgentColor(msg.agentType),
                                        animation: 'blink 1s infinite',
                                        marginRight: 8
                                      }} />
                                      <span style={{
                                        fontSize: 12,
                                        color: '#8c8c8c'
                                      }}>
                                        已输出 {msg.content.length} 字符
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                      </div>

                      {/* 用户反馈区域 */}
                      {(agentMessages.some(msg => msg.agentType === 'testcase_agent') && waitingForFeedback && roundNumber <= maxRounds) && (
                        <div style={{
                          background: '#fff7e6',
                          padding: 20,
                          borderRadius: 8,
                          border: '1px solid #ffd591',
                          marginTop: 24
                        }}>
                          <div style={{ marginBottom: 12 }}>
                            <Text strong>反馈意见 (第 {roundNumber}/{maxRounds} 轮)</Text>
                            {loading && (
                              <Text style={{ marginLeft: 8, color: '#1890ff', fontSize: 12 }}>
                                正在处理反馈...
                              </Text>
                            )}
                          </div>
                          <TextArea
                            value={userFeedback}
                            onChange={(e) => {
                              console.log('用户反馈输入:', e.target.value);
                              setUserFeedback(e.target.value);
                            }}
                            placeholder="请提出您的修改意见，或输入'同意'确认当前测试用例..."
                            rows={3}
                            disabled={loading}
                            autoFocus={!loading}
                            style={{
                              marginBottom: 12,
                              backgroundColor: loading ? '#f5f5f5' : 'white',
                              border: '1px solid #d9d9d9'
                            }}
                          />
                          <Button
                            type="primary"
                            icon={<SendOutlined />}
                            onClick={() => {
                              console.log('提交反馈按钮点击，反馈内容:', userFeedback);
                              submitFeedback();
                            }}
                            loading={loading}
                            disabled={!userFeedback.trim() || loading}
                            style={{
                              background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                              border: 'none',
                              borderRadius: 6
                            }}
                          >
                            {loading ? '处理中...' : '提交反馈'}
                          </Button>
                        </div>
                      )}

                      {/* 完成状态 */}
                      {isComplete && (
                        <div style={{
                          background: '#f6ffed',
                          padding: 20,
                          borderRadius: 8,
                          border: '1px solid #b7eb8f',
                          marginTop: 24,
                          textAlign: 'center'
                        }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24, marginBottom: 8 }} />
                          <div>
                            <Text strong style={{ color: '#52c41a', display: 'block' }}>
                              测试用例生成完成！
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              您可以导出结果或开始新的分析
                            </Text>
                          </div>
                        </div>
                      )}

                      <div ref={messagesEndRef} />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 输入区域 - 始终显示在欢迎页面 */}
            {agentMessages.length === 0 && !loading && !currentAgent && (
              <div style={{
                backgroundColor: 'white',
                borderRadius: '20px',
                padding: '24px',
                marginTop: '20px'
              }}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ fontSize: 16 }}>快速开始</Text>
                </div>

                <div style={{ marginBottom: 16 }}>
                  <FileUpload onFilesChange={handleFilesChange} />
                </div>

                <TextArea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder="描述您的测试需求，或上传需求文档..."
                  rows={3}
                  disabled={loading}
                  style={{ marginBottom: 16 }}
                />

                <Button
                  type="primary"
                  icon={<BulbOutlined />}
                  onClick={generateTestCase}
                  loading={loading}
                  size="large"
                  disabled={!textContent.trim() && selectedFiles.length === 0}
                  style={{
                    width: '100%',
                    height: 48,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 16,
                    fontWeight: 600
                  }}
                >
                  {loading ? '正在生成...' : '开始AI分析'}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CSS 样式 */}
      <style>{`
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(24, 144, 255, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(24, 144, 255, 0);
          }
        }

        @keyframes blink {
          0%, 50% {
            opacity: 1;
          }
          51%, 100% {
            opacity: 0.3;
          }
        }
      `}</style>
    </PageLayout>
  );
};

export default TestCasePage;
