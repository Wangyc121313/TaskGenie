import { Platform } from 'react-native';

/**
 * API 地址配置
 *
 * 修改 ACTIVE_ENV 切换环境，无需改动业务代码：
 *   'emulator'   — Android 模拟器 (10.0.2.2)
 *   'ios'        — iOS 模拟器 (localhost)
 *   'device'     — 真机调试，填入开发机 IP
 *   'production' — 生产环境
 */
const ENDPOINTS = {
  emulator: 'http://10.0.2.2:8000',
  ios: 'http://localhost:8000',
  device: 'http://192.168.1.100:8000', // 替换为实际开发机 IP
  production: 'https://api.taskgenie.app',
};

// 根据平台自动选择默认值，也可手动覆盖
const AUTO_ENV = Platform.OS === 'ios' ? 'ios' : 'emulator';

export const ACTIVE_ENV = AUTO_ENV; // ← 手动切换环境时修改此处

export const API_URL = ENDPOINTS[ACTIVE_ENV];
