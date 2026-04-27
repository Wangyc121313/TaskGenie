/**
 * useAgentJob
 *
 * 封装 Agent job 的启动 + 轮询生命周期，供所有 AI Modal 统一使用。
 *
 * 用法：
 *   const { jobId, running, result, error, start, reset } = useAgentJob({
 *     onComplete: (jobResult) => doSomethingWith(jobResult),
 *   });
 *
 *   // 启动（传入 AgentRunRequest payload）
 *   await start({ mode: 'schedule_day', date: '2026-04-21', ... });
 *
 * 轮询间隔: 2s，超时: 60s (30次)
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert } from 'react-native';

import { apiFetch } from '../utils/api';

const POLL_INTERVAL_MS = 2000;
const MAX_ATTEMPTS = 30; // 60s 超时

export const useAgentJob = ({ onComplete } = {}) => {
  const [jobId, setJobId] = useState(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  // 启动 Agent run
  const start = useCallback(async (payload) => {
    setRunning(true);
    setResult(null);
    setError(null);
    try {
      const { ok, data } = await apiFetch('/ai/agent/run', {
        method: 'POST',
        body: payload,
      });
      if (!ok) {
        const msg = data?.detail || data?.error || 'AI 任务启动失败';
        setError(msg);
        Alert.alert('错误', msg);
        setRunning(false);
        return null;
      }
      setJobId(data.job_id);
      return data.job_id;
    } catch (err) {
      const msg = '无法连接服务器，请确认 API 已启动。';
      setError(msg);
      Alert.alert('错误', msg);
      setRunning(false);
      return null;
    }
  }, []);

  // 轮询
  useEffect(() => {
    if (!jobId) return undefined;

    let attempts = 0;

    const timer = setInterval(async () => {
      attempts += 1;
      try {
        const { ok, data: job } = await apiFetch(`/ai/agent/runs/${jobId}`);
        if (!ok) {
          if (attempts >= MAX_ATTEMPTS) {
            setJobId(null);
            setRunning(false);
            setError('连接失败');
            Alert.alert('连接失败', '无法检查 AI 任务状态，请确认 API 已启动。');
          }
          return;
        }

        if (job.status === 'completed') {
          setJobId(null);
          setRunning(false);
          setResult(job);
          onCompleteRef.current?.(job);
        } else if (job.status === 'failed') {
          setJobId(null);
          setRunning(false);
          const msg = job.error || 'AI 任务执行失败，请重试。';
          setError(msg);
          Alert.alert('AI 执行失败', msg);
        } else if (attempts >= MAX_ATTEMPTS) {
          setJobId(null);
          setRunning(false);
          setError('超时');
          Alert.alert('超时', 'AI 任务解析超时，请检查 API 状态后重试。');
        }
      } catch (err) {
        console.error('Failed to poll agent job:', err);
        if (attempts >= MAX_ATTEMPTS) {
          setJobId(null);
          setRunning(false);
        }
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [jobId]);

  const reset = useCallback(() => {
    setJobId(null);
    setRunning(false);
    setResult(null);
    setError(null);
  }, []);

  return { jobId, running, result, error, start, reset };
};
