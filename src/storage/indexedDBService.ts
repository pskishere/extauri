// IndexedDB服务，用于本地存储画布数据

// 简化的类型定义，避免复杂的Excalidraw类型导入
interface ExcalidrawElement {
  id: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  angle: number;
  strokeColor: string;
  backgroundColor: string;
  fillStyle: string;
  strokeWidth: number;
  strokeStyle: string;
  roughness: number;
  opacity: number;
  groupIds: string[];
  frameId: string | null;
  index: string;
  roundness: any;
  seed: number;
  version: number;
  versionNonce: number;
  isDeleted: boolean;
  boundElements: any;
  updated: number;
  link: string | null;
  locked: boolean;
  [key: string]: any; // 允许其他属性
}

interface AppState {
  theme?: string;
  zoom?: { value: number };
  viewBackgroundColor?: string;
  gridModeEnabled?: boolean;
  currentItemStrokeColor?: string;
  currentItemStrokeWidth?: number;
  [key: string]: any; // 允许其他属性
}

interface CanvasData {
  elements: ExcalidrawElement[];
  appState: Partial<AppState>;
  timestamp: number;
}

class IndexedDBService {
  private dbName = 'ExcalidrawCanvas';
  private version = 1;
  private storeName = 'canvasData';
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => {
        console.error('IndexedDB打开失败:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB初始化成功');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // 创建对象存储
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          console.log('IndexedDB对象存储创建成功');
        }
      };
    });
  }

  async saveCanvasData(elements: ExcalidrawElement[], appState: Partial<AppState>): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);

      const canvasData: CanvasData & { id: string } = {
        id: 'current',
        elements,
        appState,
        timestamp: Date.now()
      };

      const request = store.put(canvasData);

      request.onsuccess = () => {
        console.log('画布数据保存到IndexedDB成功');
        resolve();
      };

      request.onerror = () => {
        console.error('画布数据保存失败:', request.error);
        reject(request.error);
      };
    });
  }

  async loadCanvasData(): Promise<CanvasData | null> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.get('current');

      request.onsuccess = () => {
        const result = request.result;
        if (result) {
          console.log('从IndexedDB加载画布数据成功:', result);
          resolve({
            elements: result.elements,
            appState: result.appState,
            timestamp: result.timestamp
          });
        } else {
          console.log('IndexedDB中没有找到画布数据');
          resolve(null);
        }
      };

      request.onerror = () => {
        console.error('从IndexedDB加载画布数据失败:', request.error);
        reject(request.error);
      };
    });
  }

  async clearCanvasData(): Promise<void> {
    if (!this.db) {
      await this.init();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.delete('current');

      request.onsuccess = () => {
        console.log('IndexedDB画布数据清除成功');
        resolve();
      };

      request.onerror = () => {
        console.error('IndexedDB画布数据清除失败:', request.error);
        reject(request.error);
      };
    });
  }

  async getLastUpdateTime(): Promise<number | null> {
    const data = await this.loadCanvasData();
    return data ? data.timestamp : null;
  }

  // 数据冲突处理：比较时间戳，返回是否应该更新
  async shouldUpdateData(newTimestamp: number): Promise<boolean> {
    try {
      const lastUpdate = await this.getLastUpdateTime();
      if (!lastUpdate) {
        return true; // 没有本地数据，直接更新
      }

      // 如果新数据比本地数据新，则更新
      return newTimestamp > lastUpdate;
    } catch (error) {
      console.error('检查数据更新时间失败:', error);
      return true; // 出错时默认更新
    }
  }

  // 安全保存：带冲突检测的保存
  async safelyUpdateCanvasData(elements: ExcalidrawElement[], appState: Partial<AppState>, sourceTimestamp?: number): Promise<boolean> {
    try {
      // 检查是否应该更新
      if (sourceTimestamp && !(await this.shouldUpdateData(sourceTimestamp))) {
        console.log('⏭️ 数据时间戳较旧，跳过更新');
        return false;
      }

      await this.saveCanvasData(elements, appState);
      console.log('✅ 数据安全更新成功');
      return true;
    } catch (error) {
      console.error('❌ 安全更新失败:', error);
      return false;
    }
  }

  // 错误恢复：尝试修复损坏的数据
  async repairData(): Promise<boolean> {
    try {
      console.log('🔧 开始数据修复...');

      // 尝试加载数据
      const data = await this.loadCanvasData();
      if (!data) {
        console.log('📭 没有数据需要修复');
        return true;
      }

      // 验证数据完整性
      if (!Array.isArray(data.elements)) {
        console.log('🔧 修复元素数组...');
        data.elements = [];
      }

      if (!data.appState || typeof data.appState !== 'object') {
        console.log('🔧 修复应用状态...');
        data.appState = {};
      }

      if (!data.timestamp || typeof data.timestamp !== 'number') {
        console.log('🔧 修复时间戳...');
        data.timestamp = Date.now();
      }

      // 重新保存修复后的数据
      await this.saveCanvasData(data.elements, data.appState);
      console.log('✅ 数据修复完成');
      return true;
    } catch (error) {
      console.error('❌ 数据修复失败:', error);
      // 如果修复失败，清空数据重新开始
      try {
        await this.clearCanvasData();
        console.log('🗑️ 已清空损坏的数据');
        return true;
      } catch (clearError) {
        console.error('❌ 清空数据也失败:', clearError);
        return false;
      }
    }
  }
}

// 导出单例实例
export const indexedDBService = new IndexedDBService();
export default indexedDBService;