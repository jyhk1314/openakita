/**
 * 研发统一服务（产品公共服务 IP + 固定端口 10001）HTTP 接口。
 *
 * 约定：仅 **Tauri 桌面模式** 会访问研发统一服务；非 Tauri 环境不应调用本模块（由调用方分支处理）。
 * - 服务地址：`~/.synapse/devservice.ip`（Synapse 用户根）中的真实 IP，仅通过 Tauri `read_devservice_ip` 读取。
 * - `owner_info` / 姓名：仍通过本机 Synapse `GET /api/dev/userinfo-for-unified-service`（桌面通常带本地后端）。
 */

import { IS_TAURI, invoke, proxyFetch } from "@/platform";

/** 研发统一服务固定端口（与引导「产品公共服务」一致） */
export const RD_UNIFIED_PORT = 10001;

export const RD_UNIFIED_PATHS = {
  insertProdInfo: "/dev/iwhalecloud/synapse/create_prod",
  updateProdInfo: "/dev/iwhalecloud/synapse/update_prod_info",
  getProdInfo: "/dev/iwhalecloud/synapse/get_prod_info",
  getProdProcessInfo: "/dev/iwhalecloud/synapse/get_prod_process_info",
  changeRepoInfo: "/dev/iwhalecloud/synapse/change_repo_info",
} as const;

export type RdRepoInfo = {
  repo_url: string;
  repo_branch: string;
  repo_func: string;
  repo_token: string;
  repo_master: "Y" | "N";
};

/** 仓库分析进度（多仓库按优先级聚合展示）；repo_process_state 单字符 N/I/P/D/E/F（见 normalizeWireProcessState） */
export type RepoProcessWireItem = {
  repo_branch: string;
  repo_process_state: string;
  /** 分析完成时间（状态为 D 时由服务端返回，可选） */
  repo_process_time?: string | null;
};

/** 文档维度进度（多文档类型按优先级聚合）；doc_process_state 单字符与仓库一致 */
export type DocProcessWireItem = {
  doc_type: string;
  doc_process_state: string;
  /** 该类型文档分析完成时间（状态为 D 时可选） */
  doc_process_time?: string | null;
};

export type InsertProdInfoBody = {
  prod: string;
  version: string;
  module: string;
  space: string;
  owner: string;
  function: string;
  prod_icon: string;
  prod_desc: string;
  owner_info: string;
  repo_info: RdRepoInfo[];
};

/** 研发统一服务通用 JSON 响应（insert / update 等） */
export type DevServiceResponse = {
  code: number;
  data: unknown;
  message: string;
  total: number;
};

export type UpdateProdInfoBody = {
  prod: string;
  function: string;
  /** 图标标识字符串，服务端据此解析实际图标 */
  prod_icon: string;
  /** 产品描述 */
  prod_desc: string;
};

/** 研发统一服务 get_prod_info 单条记录（与 insert 字段对齐）；部分字段服务端可能为 null */
export type ProdInfoWireItem = {
  prod: string | null;
  version: string | null;
  module: string | null;
  space: string | null;
  owner: string | null;
  /** 产品功能（与创建时 function 一致） */
  function: string | null;
  /** 图标标识字符串，前端用 DEFAULT_ICONS label 等规则解析为展示用图标 */
  prod_icon: string | null;
  prod_desc: string | null;
  owner_info: string | null;
  repo_info: RdRepoInfo[] | null;
  /** 各仓库处理状态；多条时按 error > init > process > new > done 聚合（见 pickWorstUnifiedState） */
  repo_process?: RepoProcessWireItem[];
  /** 工单维度单值；字符含义与 repo_process_state 一致 */
  order_process?: string;
  /** 工单分析完成时间（order_process 为 D 时可选） */
  order_process_time?: string | null;
  /** 各文档类型处理状态；聚合规则与 repo_process 相同 */
  doc_process?: DocProcessWireItem[];
};

/** get_prod_info 完整响应；total 为查询到的产品条数，一般与 data.length 一致，不做分页 */
export type GetProdInfoResponse = {
  code: number;
  data: ProdInfoWireItem[] | null;
  message: string;
  total: number;
};

/** get_prod_process_info 入参 */
export type GetProdProcessInfoBody = {
  prod: string;
};

/** get_prod_process_info 的 data 载荷（与列表项中的过程字段一致） */
export type ProdProcessDataPayload = {
  repo_process?: RepoProcessWireItem[];
  order_process?: string;
  order_process_time?: string | null;
  doc_process?: DocProcessWireItem[];
};

export type GetProdProcessInfoResponse = {
  code: number;
  data: ProdProcessDataPayload | null;
  message: string;
  total: number;
};

/** change_repo_info：服务端若需产品标识可一并传 prod */
export type ChangeRepoInfoBody = {
  prod: string;
  repo_info: RdRepoInfo[];
};

function rdUnifiedOrigin(host: string): string {
  const h = host.trim();
  if (!h) {
    throw new Error("missing_devservice_host");
  }
  if (h.includes("://")) {
    try {
      const u = new URL(h);
      return `${u.protocol}//${u.hostname}:${RD_UNIFIED_PORT}`;
    } catch {
      throw new Error("invalid_devservice_host");
    }
  }
  const isV4 = /^\d{1,3}(\.\d{1,3}){3}$/.test(h);
  const hostPart = !isV4 && h.includes(":") ? `[${h}]` : h;
  return `http://${hostPart}:${RD_UNIFIED_PORT}`;
}

async function fetchSynapseJson<T>(
  synapseApiBase: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const base = synapseApiBase.replace(/\/$/, "");
  const res = await fetch(`${base}${path}`, {
    ...init,
    signal: init?.signal ?? AbortSignal.timeout(30_000),
  });
  const j = (await res.json()) as { errorcode?: number; message?: string; data?: T };
  if (j.errorcode !== 0) {
    throw new Error(j.message || "synapse_api_error");
  }
  return j.data as T;
}

/**
 * 从 `synapse_root/devservice.ip`（如 `~/.synapse/devservice.ip`）读取产品公共服务真实 IP（仅 Tauri）。
 * 非 Tauri 返回 `null`，调用方不应依赖 Web 降级路径访问 10001。
 */
export async function getDevserviceHost(): Promise<string | null> {
  if (!IS_TAURI) return null;
  try {
    const ip = await invoke<string | null>("read_devservice_ip");
    return ip?.trim() || null;
  } catch {
    return null;
  }
}

export async function fetchUserinfoForUnifiedService(synapseApiBase: string): Promise<{
  owner_info: string;
  owner_name: string;
}> {
  return fetchSynapseJson(synapseApiBase, "/api/dev/userinfo-for-unified-service");
}

/** POST 研发统一服务（Tauri `http_proxy_request`） */
export async function postRdUnifiedJson<T>(
  host: string,
  relativePath: string,
  body: unknown,
): Promise<T> {
  const url = `${rdUnifiedOrigin(host)}${relativePath.startsWith("/") ? "" : "/"}${relativePath}`;
  const json = JSON.stringify(body);
  const { status, body: text } = await proxyFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: json,
    timeoutSecs: 60,
  });
  let parsed: T;
  try {
    parsed = JSON.parse(text) as T;
  } catch {
    throw new Error(`rd_unified_invalid_json: HTTP ${status}`);
  }
  if (status >= 400) {
    throw new Error(`rd_unified_http_${status}`);
  }
  return parsed;
}

/**
 * 创建产品：调用研发统一服务 insert_prod_info，并自动附带 owner_info / owner。
 * 仅应在 Tauri 下调用（依赖 `read_devservice_ip` 与 `proxyFetch`）。
 */
export async function insertProdInfo(
  synapseApiBase: string,
  input: Omit<InsertProdInfoBody, "owner_info" | "owner"> & { owner?: string },
): Promise<DevServiceResponse> {
  if (!IS_TAURI) {
    throw new Error("rd_unified_tauri_only");
  }
  const host = await getDevserviceHost();
  if (!host) {
    throw new Error("missing_devservice_ip");
  }
  const { owner_info, owner_name } = await fetchUserinfoForUnifiedService(synapseApiBase);
  const owner = (input.owner ?? owner_name ?? "").trim();
  const payload: InsertProdInfoBody = {
    ...input,
    owner,
    owner_info,
  };
  const resp = await postRdUnifiedJson<DevServiceResponse>(
    host,
    RD_UNIFIED_PATHS.insertProdInfo,
    payload,
  );
  if (resp.code !== 0) {
    throw new Error(resp.message || "insert_prod_failed");
  }
  return resp;
}

/**
 * 更新产品信息：研发统一服务 update_prod_info（prod / function / prod_icon / prod_desc）。
 * 仅应在 Tauri 下调用。
 */
export async function updateProdInfo(
  _synapseApiBase: string,
  body: UpdateProdInfoBody,
): Promise<DevServiceResponse> {
  if (!IS_TAURI) {
    throw new Error("rd_unified_tauri_only");
  }
  const host = await getDevserviceHost();
  if (!host) {
    throw new Error("missing_devservice_ip");
  }
  const resp = await postRdUnifiedJson<DevServiceResponse>(
    host,
    RD_UNIFIED_PATHS.updateProdInfo,
    body,
  );
  if (resp.code !== 0) {
    throw new Error(resp.message || "update_prod_failed");
  }
  return resp;
}

/**
 * 查询产品列表：研发统一服务 get_prod_info，无请求体。
 * 仅应在 Tauri 下调用。数据量通常较小，一次性拉全量、不分页。
 */
export async function getProdInfo(_synapseApiBase: string): Promise<GetProdInfoResponse> {
  if (!IS_TAURI) {
    throw new Error("rd_unified_tauri_only");
  }
  const host = await getDevserviceHost();
  if (!host) {
    throw new Error("missing_devservice_ip");
  }
  const resp = await postRdUnifiedJson<GetProdInfoResponse>(host, RD_UNIFIED_PATHS.getProdInfo, {});
  if (resp.code !== 0) {
    throw new Error(resp.message || "get_prod_failed");
  }
  return resp;
}

/**
 * 查询单产品分析过程状态：get_prod_process_info，body `{ prod }`。
 * 仅应在 Tauri 下调用。
 */
export async function getProdProcessInfo(
  _synapseApiBase: string,
  body: GetProdProcessInfoBody,
): Promise<GetProdProcessInfoResponse> {
  if (!IS_TAURI) {
    throw new Error("rd_unified_tauri_only");
  }
  const host = await getDevserviceHost();
  if (!host) {
    throw new Error("missing_devservice_ip");
  }
  const resp = await postRdUnifiedJson<GetProdProcessInfoResponse>(
    host,
    RD_UNIFIED_PATHS.getProdProcessInfo,
    body,
  );
  if (resp.code !== 0) {
    throw new Error(resp.message || "get_prod_process_failed");
  }
  return resp;
}

/**
 * 更新产品仓库配置。
 *
 * **路径**：`POST {devservice}:10001/dev/iwhalecloud/synapse/change_repo_info`（见 {@link RD_UNIFIED_PATHS.changeRepoInfo}）
 *
 * **请求体**：
 * - `prod`：产品名称
 * - `repo_info`：`{ repo_url, repo_branch, repo_func, repo_token, repo_master: "Y"|"N" }[]`
 *
 * 成功后可由调用方再调 {@link getProdProcessInfo} 刷新过程状态。
 */
export async function changeRepoInfo(
  _synapseApiBase: string,
  body: ChangeRepoInfoBody,
): Promise<DevServiceResponse> {
  if (!IS_TAURI) {
    throw new Error("rd_unified_tauri_only");
  }
  const host = await getDevserviceHost();
  if (!host) {
    throw new Error("missing_devservice_ip");
  }
  const resp = await postRdUnifiedJson<DevServiceResponse>(
    host,
    RD_UNIFIED_PATHS.changeRepoInfo,
    body,
  );
  if (resp.code !== 0) {
    throw new Error(resp.message || "change_repo_failed");
  }
  return resp;
}
