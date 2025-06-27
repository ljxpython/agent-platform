/**
 * UI测试相关API接口
 */

import { request } from '../utils/request';

export interface ImageUploadRequest {
  user_requirement: string;
  collection_name?: string;
  user_id?: string;
}

export interface UITestingQueryRequest {
  user_requirement: string;
  collection_name?: string;
  user_id?: string;
}

export interface UploadResponse {
  code: number;
  msg: string;
  data: {
    conversation_id: string;
    uploaded_files: number;
    file_paths: string[];
    collection_name: string;
    user_requirement: string;
  };
}

export interface QueryResponse {
  code: number;
  msg: string;
  data: {
    conversation_id: string;
    rag_answer: string;
    retrieved_docs: any[];
    user_requirement: string;
    collection_name: string;
  };
}

export interface CollectionInfo {
  id: number;
  name: string;
  display_name: string;
  description: string;
  business_type: string;
  document_count: number;
  created_at: string;
}

export interface CollectionsResponse {
  code: number;
  msg: string;
  data: {
    collections: CollectionInfo[];
  };
}

/**
 * 上传UI界面图片进行分析
 */
export const uploadUIImages = async (
  files: File[],
  userRequirement: string,
  collectionName: string = 'ui_testing',
  userId: string = 'anonymous'
): Promise<UploadResponse> => {
  const formData = new FormData();

  // 添加文件
  files.forEach(file => {
    formData.append('files', file);
  });

  // 添加其他参数
  formData.append('user_requirement', userRequirement);
  formData.append('collection_name', collectionName);
  formData.append('user_id', userId);

  return request.post('/ui-test/image-analysis/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

/**
 * 查询UI分析进度
 */
export const getAnalysisProgress = (conversationId: string): EventSource => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const url = `${baseURL}/api/v1/ui-test/image-analysis/progress/${conversationId}`;

  return new EventSource(url);
};

/**
 * 基于RAG知识库的UI测试查询
 */
export const queryUITestingWithRAG = async (
  queryRequest: UITestingQueryRequest
): Promise<QueryResponse> => {
  return request.post('/ui-test/rag-query/query', queryRequest);
};

/**
 * 获取UI测试相关的Collection列表
 */
export const getUITestingCollections = async (): Promise<CollectionsResponse> => {
  return request.get('/ui-test/collections/');
};

/**
 * 清理分析产生的图片文件
 */
export const cleanupAnalysisImages = async (conversationId: string): Promise<any> => {
  return request.delete(`/ui-test/image-analysis/cleanup/${conversationId}`);
};

/**
 * 创建SSE连接监听分析进度
 */
export const createProgressListener = (
  conversationId: string,
  onMessage: (data: any) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): EventSource => {
  const eventSource = getAnalysisProgress(conversationId);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('解析SSE消息失败:', error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error);
    if (onError) {
      onError(error);
    }
  };

  eventSource.addEventListener('close', () => {
    eventSource.close();
    if (onClose) {
      onClose();
    }
  });

  return eventSource;
};

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 验证图片文件类型
 */
export const validateImageFile = (file: File): boolean => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
  return allowedTypes.includes(file.type);
};

/**
 * 验证文件大小（默认最大10MB）
 */
export const validateFileSize = (file: File, maxSizeMB: number = 10): boolean => {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};
