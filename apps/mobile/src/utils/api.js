/**
 * apiFetch — 统一 API 请求层
 *
 * 封装：
 *  - BASE URL 注入（来自 config.js，单一配置点）
 *  - Content-Type: application/json 默认头
 *  - body 自动 JSON.stringify（传对象即可，也可传已序列化的字符串）
 *  - 统一返回 { ok, status, data }，方便 hooks 做错误判断
 *
 * 用法：
 *   const { ok, data } = await apiFetch('/tasks', { method: 'POST', body: taskData });
 */

import { API_URL } from './config';

export async function apiFetch(path, options = {}) {
  const { body, headers, ...rest } = options;

  const fetchOptions = {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (body !== undefined) {
    fetchOptions.body =
      typeof body === 'string' ? body : JSON.stringify(body);
  }

  const response = await fetch(`${API_URL}${path}`, fetchOptions);
  const data = await response.json().catch(() => ({}));

  return { ok: response.ok, status: response.status, data };
}
