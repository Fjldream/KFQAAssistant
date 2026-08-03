import { ref, type Ref } from "vue";
import { createApiClient } from "../api/client";
import type { ApiSettings, HealthResponse, IndexStatusResponse, ReadinessResponse } from "../api/types";

export interface IndexStatusClient {
  health: () => Promise<HealthResponse>;
  readiness: () => Promise<ReadinessResponse>;
  indexStatus: () => Promise<IndexStatusResponse>;
}

// 将未知错误转换为状态区域可读的错误文案。
function toStatusErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "状态检查失败，请确认后端服务是否可用。";
}

// 根据当前设置创建状态检查客户端，测试时允许注入假客户端。
function resolveClient(settings: Ref<ApiSettings>, injectedClient?: IndexStatusClient): IndexStatusClient {
  return injectedClient ?? createApiClient(settings.value);
}

// 管理后端健康检查、就绪检查和索引状态加载。
export function useIndexStatus(
  settings: Ref<ApiSettings>,
  injectedClient?: IndexStatusClient,
): {
  health: Ref<HealthResponse | null>;
  readiness: Ref<ReadinessResponse | null>;
  indexStatus: Ref<IndexStatusResponse | null>;
  isLoading: Ref<boolean>;
  errorMessage: Ref<string | null>;
  refresh: () => Promise<void>;
} {
  const health = ref<HealthResponse | null>(null);
  const readiness = ref<ReadinessResponse | null>(null);
  const indexStatus = ref<IndexStatusResponse | null>(null);
  const isLoading = ref(false);
  const errorMessage = ref<string | null>(null);

  async function refresh(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = null;
    const client = resolveClient(settings, injectedClient);
    try {
      const [healthResponse, readinessResponse, indexStatusResponse] = await Promise.all([
        client.health(),
        client.readiness(),
        client.indexStatus(),
      ]);
      health.value = healthResponse;
      readiness.value = readinessResponse;
      indexStatus.value = indexStatusResponse;
    } catch (error) {
      errorMessage.value = toStatusErrorMessage(error);
    } finally {
      isLoading.value = false;
    }
  }

  return {
    health,
    readiness,
    indexStatus,
    isLoading,
    errorMessage,
    refresh,
  };
}
