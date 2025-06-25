import React, { useState, useEffect, useRef } from 'react';
import { Button, Card, Typography, Space, message } from 'antd';
import PageLayout from '@/components/PageLayout';

const { Title, Text } = Typography;

interface TestMessage {
  id: string;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

const ScrollTestPage: React.FC = () => {
  const [messages, setMessages] = useState<TestMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUserScrolling, setIsUserScrolling] = useState<boolean>(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState<boolean>(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const lastScrollTop = useRef<number>(0);
  const isAutoScrolling = useRef<boolean>(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    if (shouldAutoScroll && !isUserScrolling && messagesEndRef.current) {
      isAutoScrolling.current = true;
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });

      setTimeout(() => {
        isAutoScrolling.current = false;
      }, 1000);
    }
  };

  // 检查是否在底部
  const isAtBottom = () => {
    if (!messagesContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    return scrollHeight - scrollTop - clientHeight < 100;
  };

  // 检测用户是否在滚动
  const handleScroll = () => {
    if (!messagesContainerRef.current || isAutoScrolling.current) return;

    const container = messagesContainerRef.current;
    const currentScrollTop = container.scrollTop;

    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    const isScrollingUp = currentScrollTop < lastScrollTop.current;
    const isScrollingDown = currentScrollTop > lastScrollTop.current;

    if (isScrollingUp) {
      setIsUserScrolling(true);
      setShouldAutoScroll(false);
    } else if (isScrollingDown && isAtBottom()) {
      setIsUserScrolling(false);
      setShouldAutoScroll(true);
    }

    lastScrollTop.current = currentScrollTop;

    scrollTimeoutRef.current = setTimeout(() => {
      if (isAtBottom()) {
        setIsUserScrolling(false);
        setShouldAutoScroll(true);
      }
    }, 150);
  };

  // 只在新消息到达且应该自动滚动时才滚动
  useEffect(() => {
    if (messages.length > 0 && shouldAutoScroll && !isUserScrolling) {
      requestAnimationFrame(() => {
        scrollToBottom();
      });
    }
  }, [messages.length, shouldAutoScroll, isUserScrolling]);

  // 添加滚动事件监听
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll, { passive: true });
      return () => {
        container.removeEventListener('scroll', handleScroll);
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
      };
    }
  }, []);

  // 添加测试消息
  const addMessage = (content: string) => {
    const newMessage: TestMessage = {
      id: Date.now().toString(),
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  // 模拟流式输出
  const simulateStreaming = async () => {
    if (isStreaming) return;

    setIsStreaming(true);
    const streamingMessage: TestMessage = {
      id: Date.now().toString(),
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, streamingMessage]);

    const fullText = "这是一个模拟的流式输出测试。我会逐字显示这段文本，就像真实的AI对话一样。你可以在输出过程中尝试滚动页面，看看是否会被强制拉回底部。如果滚动控制正常工作，你应该能够自由浏览历史消息而不被打断。这个测试会持续一段时间，请耐心等待并测试滚动功能。现在让我们继续添加更多内容来测试滚动行为。";

    for (let i = 0; i <= fullText.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 50));

      setMessages(prev =>
        prev.map(msg =>
          msg.id === streamingMessage.id
            ? { ...msg, content: fullText.substring(0, i) }
            : msg
        )
      );
    }

    // 完成流式输出
    setMessages(prev =>
      prev.map(msg =>
        msg.id === streamingMessage.id
          ? { ...msg, isStreaming: false }
          : msg
      )
    );

    setIsStreaming(false);
    message.success('流式输出完成！');
  };

  // 清空消息
  const clearMessages = () => {
    setMessages([]);
    setIsUserScrolling(false);
    setShouldAutoScroll(true);
  };

  return (
    <PageLayout>
      <div style={{ padding: '24px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Title level={2}>滚动控制测试页面</Title>

        <Card style={{ marginBottom: '16px' }}>
          <Space wrap>
            <Button onClick={() => addMessage('这是一条测试消息 #' + (messages.length + 1))}>
              添加消息
            </Button>
            <Button onClick={simulateStreaming} loading={isStreaming} type="primary">
              模拟流式输出
            </Button>
            <Button onClick={clearMessages}>
              清空消息
            </Button>
            <Text>
              自动滚动: {shouldAutoScroll ? '✅ 开启' : '❌ 关闭'}
            </Text>
            <Text>
              用户滚动: {isUserScrolling ? '✅ 是' : '❌ 否'}
            </Text>
          </Space>
        </Card>

        <Card
          title="测试说明"
          style={{ marginBottom: '16px' }}
          size="small"
        >
          <Text>
            1. 点击"模拟流式输出"开始测试<br/>
            2. 在流式输出过程中，尝试向上滚动查看历史消息<br/>
            3. 如果滚动控制正常，你应该能够自由浏览而不被强制拉回底部<br/>
            4. 滚动到底部时，自动滚动会重新启用<br/>
            5. 点击右下角的"↓"按钮可以手动回到底部
          </Text>
        </Card>

        <Card
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}
        >
          <div style={{ position: 'relative', flex: 1, overflow: 'hidden' }}>
            <div
              ref={messagesContainerRef}
              style={{
                height: '100%',
                overflowY: 'auto',
                padding: '16px',
                backgroundColor: '#fafafa'
              }}
            >
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  style={{
                    marginBottom: '12px',
                    padding: '12px',
                    backgroundColor: 'white',
                    borderRadius: '8px',
                    border: message.isStreaming ? '2px solid #1890ff' : '1px solid #d9d9d9'
                  }}
                >
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                    消息 #{index + 1} - {message.timestamp.toLocaleTimeString()}
                    {message.isStreaming && <span style={{ color: '#1890ff' }}> (流式输出中...)</span>}
                  </div>
                  <div>{message.content}</div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* 滚动控制按钮 */}
            {!shouldAutoScroll && (
              <div style={{
                position: 'absolute',
                bottom: 16,
                right: 16,
                zIndex: 1000
              }}>
                <Button
                  type="primary"
                  shape="circle"
                  size="small"
                  icon={<div style={{ fontSize: 12 }}>↓</div>}
                  onClick={() => {
                    setIsUserScrolling(false);
                    setShouldAutoScroll(true);
                    isAutoScrolling.current = true;
                    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
                    setTimeout(() => {
                      isAutoScrolling.current = false;
                    }, 1000);
                  }}
                  style={{
                    backgroundColor: '#1890ff',
                    borderColor: '#1890ff',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                  }}
                  title="回到底部"
                />
              </div>
            )}
          </div>
        </Card>
      </div>
    </PageLayout>
  );
};

export default ScrollTestPage;
