/**
 * 错误处理工具
 * 用于处理浏览器扩展冲突等问题
 */

// 防止浏览器扩展冲突
export const setupErrorHandling = () => {
  // 捕获并忽略TronLink等钱包扩展的错误
  const originalError = console.error;
  console.error = function(...args: any[]) {
    const message = args[0];
    if (typeof message === 'string' && 
        (message.includes('tronLink') || 
         message.includes('Cannot assign to read only property') ||
         message.includes('chrome-extension://') ||
         message.includes('ethereum') ||
         message.includes('web3'))) {
      // 忽略钱包扩展相关的错误
      return;
    }
    originalError.apply(console, args);
  };

  // 防止扩展覆盖全局对象
  window.addEventListener('error', function(event) {
    if (event.message && 
        (event.message.includes('tronLink') || 
         event.message.includes('Cannot assign to read only property') ||
         event.message.includes('ethereum') ||
         event.message.includes('web3'))) {
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  });

  // 防止未处理的Promise拒绝
  window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && 
        event.reason.message && 
        (event.reason.message.includes('tronLink') || 
         event.reason.message.includes('Cannot assign to read only property') ||
         event.reason.message.includes('ethereum') ||
         event.reason.message.includes('web3'))) {
      event.preventDefault();
      return false;
    }
  });

  // 保护window对象的关键属性
  const originalDefineProperty = Object.defineProperty;
  Object.defineProperty = function(obj: any, prop: string, descriptor: any) {
    if (obj === window && (prop === 'tronLink' || prop === 'ethereum' || prop === 'web3')) {
      // 如果属性已存在且不可写，则跳过
      if (obj.hasOwnProperty(prop) && !obj.propertyIsEnumerable(prop)) {
        return obj;
      }
    }
    return originalDefineProperty.call(this, obj, prop, descriptor);
  };
};

// 检查是否是钱包扩展错误
export const isWalletExtensionError = (error: any): boolean => {
  if (!error) return false;
  
  const message = error.message || error.toString();
  return message.includes('tronLink') || 
         message.includes('Cannot assign to read only property') ||
         message.includes('chrome-extension://') ||
         message.includes('ethereum') ||
         message.includes('web3');
};

// 安全地访问钱包对象
export const safeAccessWallet = (walletName: string) => {
  try {
    return (window as any)[walletName];
  } catch (error) {
    if (isWalletExtensionError(error)) {
      console.warn(`钱包扩展 ${walletName} 不可用`);
      return null;
    }
    throw error;
  }
};
