/**
 * Midscene API 服务
 * 提供 Midscene 智能体系统的前端 API 接口
 */

import { request } from '@/utils/request';

// ==================== 类型定义 ====================

export interface MidsceneGenerateRequest {
  user_requirement: string;
  conversation_id?: string;
}

export interface MidsceneUploadResponse {
  success: boolean;
  message: string;
  file_path?: string;
  file_size?: number;
}

export interface MidsceneAnalysisResponse {
  success: boolean;
  session_id: string;
  message: string;
}

export interface MidsceneStreamEvent {
  type: string;
  agent: string;
  content: string;
  step?: string;
  timestamp?: number;
}

export interface MidsceneTestResponse {
  success: boolean;
  message: string;
  version: string;
  upload_dir: string;
  supported_formats: string[];
}

// ==================== API 服务类 ====================

export class MidsceneAPI {
  /**
   * 测试 Midscene API 连接
   */
  static async test(): Promise<MidsceneTestResponse> {
    const response = await request.get<MidsceneTestResponse>('/api/midscene/test');
    return response.data;
  }

  /**
   * 上传图片文件
   */
  static async uploadImage(file: File, sessionId: string): Promise<MidsceneUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response = await request.post<MidsceneUploadResponse>('/api/midscene/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * 生成 Midscene 测试脚本（流式输出）
   */
  static async generateStreaming(
    sessionId: string,
    userRequirement: string,
    files: File[]
  ): Promise<Response> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('user_requirement', userRequirement);

    // 添加文件
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch('/api/midscene/generate/streaming', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  }

  /**
   * 启动 Midscene 分析（非流式）
   */
  static async startAnalysis(
    sessionId: string,
    userRequirement: string,
    imagePaths: string[]
  ): Promise<MidsceneAnalysisResponse> {
    const response = await request.post<MidsceneAnalysisResponse>('/api/midscene/analyze', {
      session_id: sessionId,
      user_requirement: userRequirement,
      image_paths: imagePaths,
    });
    return response.data;
  }

  /**
   * 获取流式输出
   */
  static async getStream(sessionId: string): Promise<Response> {
    const response = await fetch(`/api/midscene/stream/${sessionId}`, {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  }

  /**
   * 清理会话
   */
  static async cleanupSession(sessionId: string): Promise<{ success: boolean; message: string }> {
    const response = await request.delete<{ success: boolean; message: string }>(`/api/midscene/session/${sessionId}`);
    return response.data;
  }
}

// ==================== SSE 流式处理工具 ====================

export interface SSEEventHandler {
  onMessage?: (event: MidsceneStreamEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export class MidsceneSSEClient {
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private decoder = new TextDecoder();
  private buffer = '';

  /**
   * 处理 SSE 流
   */
  async processStream(response: Response, handlers: SSEEventHandler): Promise<void> {
    if (!response.body) {
      throw new Error('Response body is null');
    }

    this.reader = response.body.getReader();

    try {
      while (true) {
        const { done, value } = await this.reader.read();

        if (done) {
          break;
        }

        this.buffer += this.decoder.decode(value, { stream: true });
        const lines = this.buffer.split('\n');
        this.buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              handlers.onMessage?.(data);

              // 检查是否为完成事件
              if (data.type === 'system_complete' || data.type === 'system_error') {
                handlers.onComplete?.();
                return;
              }
            } catch (error) {
              console.warn('Failed to parse SSE data:', line, error);
            }
          }
        }
      }
    } catch (error) {
      handlers.onError?.(error as Error);
    } finally {
      this.cleanup();
    }
  }

  /**
   * 停止流处理
   */
  stop(): void {
    this.cleanup();
  }

  /**
   * 清理资源
   */
  private cleanup(): void {
    if (this.reader) {
      this.reader.releaseLock();
      this.reader = null;
    }
    this.buffer = '';
  }
}

// ==================== 工具函数 ====================

/**
 * 验证图片文件
 */
export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // 检查文件类型
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: '不支持的文件格式，请上传 JPG、PNG、GIF、BMP 或 WebP 格式的图片'
    };
  }

  // 检查文件大小（10MB）
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    return {
      valid: false,
      error: '文件大小超过限制，请上传小于 10MB 的图片'
    };
  }

  return { valid: true };
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 生成会话ID
 */
export function generateSessionId(): string {
  return `midscene_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 下载文本文件
 */
export function downloadTextFile(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 复制到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
}

// 导出默认实例
export default MidsceneAPI;
