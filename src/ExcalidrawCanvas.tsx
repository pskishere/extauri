import { Excalidraw } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import { listen, UnlistenFn } from "@tauri-apps/api/event";
import { useEffect, useRef, useState } from "react";
import { indexedDBService } from "./storage/indexedDBService";

// 检查是否在Tauri环境中
// @ts-ignore
const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__;

// 添加调试日志
console.log('🔍 环境检测:', {
  windowExists: typeof window !== 'undefined',
  hasTauriAPI: typeof window !== 'undefined' && !!(window as any).__TAURI__,
  isLocalhost: typeof window !== 'undefined' && window.location.hostname === 'localhost',
  isTauri: isTauri
});

type DrawPayload = {
  elements?: any;
  appState?: any;
  files?: any;
};

// 确保 collaborators 是 Map 类型的辅助函数
const ensureCollaboratorsMap = (appState: any) => {
  if (!appState) return { collaborators: new Map() };

  // 如果 collaborators 已经是 Map，直接返回
  if (appState.collaborators instanceof Map) {
    return appState;
  }

  // 如果 collaborators 是数组或其他类型，转换为 Map
  return {
    ...appState,
    collaborators: new Map()
  };
};

export function ExcalidrawCanvas() {
  const apiRef = useRef<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [canvasData, setCanvasData] = useState<any>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const isUpdatingFromRestore = useRef(false); // 防止数据恢复时触发onChange的标志
  const saveTimeoutRef = useRef<number | null>(null); // 防抖定时器
  const lastSaveDataRef = useRef<string>(''); // 上次保存的数据哈希

  // 初始化IndexedDB并恢复画布数据
  useEffect(() => {
    const initializeStorage = async () => {
      try {
        await indexedDBService.init();
        console.log('📦 IndexedDB初始化成功');

        // 尝试修复可能损坏的数据
        const repairSuccess = await indexedDBService.repairData();
        if (!repairSuccess) {
          console.warn('⚠️ 数据修复失败，将使用空画布');
        }

        // 应用启动时从后端同步数据
        let backendData = null;
        try {
          console.log('📥 应用启动时从后端同步数据...');
          const response = await fetch('http://localhost:31337/canvas');
          if (response.ok) {
            const data = await response.json();
            if (data.canvas && data.canvas.elements) {
              backendData = data.canvas;
              console.log('✅ 从后端获取到画布数据:', data.canvas.elements.length, '个元素');

              // 将后端数据保存到本地
              await indexedDBService.saveCanvasData(data.canvas.elements, data.canvas.appState || {});
              console.log('💾 后端数据已同步到本地存储');
            }
          }
        } catch (error) {
          console.warn('⚠️ 从后端同步数据失败，使用本地数据:', error);
        }

        // 优先使用后端数据，如果没有则使用本地数据
        let dataToRestore = backendData;
        if (!dataToRestore) {
          const savedData = await indexedDBService.loadCanvasData();
          if (savedData && savedData.elements) {
            dataToRestore = savedData;
            console.log('📂 使用本地IndexedDB数据:', savedData.elements.length, '个元素');
          }
        }

        if (dataToRestore && apiRef.current) {
          console.log('🔄 恢复画布数据:', dataToRestore.elements.length, '个元素');
          // 确保appState包含必需的collaborators属性
          const safeAppState = ensureCollaboratorsMap(dataToRestore.appState);

          apiRef.current.updateScene({
            elements: dataToRestore.elements,
            appState: safeAppState,
            files: dataToRestore.files || {}
          });
          console.log('✅ 画布数据恢复成功');
        } else {
          console.log('📭 没有找到可恢复的画布数据');
        }
      } catch (error) {
        console.error('❌ IndexedDB初始化失败:', error);
        // 初始化失败时尝试修复
        try {
          await indexedDBService.repairData();
          console.log('🔧 已尝试修复IndexedDB');
        } catch (repairError) {
          console.error('❌ 修复也失败:', repairError);
        }
      }
    };

    if (apiRef.current && !isInitialized) {
      initializeStorage();
      setIsInitialized(true);
    }
  }, [apiRef.current, isInitialized]);

  // 组件卸载时清理防抖定时器
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // 提取画布更新处理逻辑为独立函数
  const handleCanvasUpdate = async (payload: DrawPayload) => {
    console.log("🎨 处理画布更新:", payload);
    console.log("📦 payload:", JSON.stringify(payload, null, 2));

    if (apiRef.current) {
      console.log("✅ apiRef.current 存在，准备更新画布元素");

      try {
        // 确保元素数组存在且格式正确
        const elements = Array.isArray(payload.elements) ? payload.elements : [];
        console.log("🔍 准备更新的元素数量:", elements.length);
        console.log("🔍 元素内容:", elements);

        if (elements.length > 0) {
          // 处理元素，确保所有必需字段都存在
          const processedElements: any[] = [];

          elements.forEach((element: any, index: number) => {
            // 深度克隆元素，避免修改原始对象
            const cleanElement = { ...element };

            // 确保所有必需字段都存在且类型正确
            const baseElement = {
              ...cleanElement,
              id: cleanElement.id || `element_${Date.now()}_${index}`,
              seed: cleanElement.seed || Math.floor(Math.random() * 1000000),
              versionNonce: cleanElement.versionNonce || Math.floor(Math.random() * 1000000),
              groupIds: Array.isArray(cleanElement.groupIds) ? cleanElement.groupIds : [],
              boundElements: cleanElement.boundElements || null,
              updated: cleanElement.updated || Date.now(),
              link: cleanElement.link || null,
              locked: Boolean(cleanElement.locked),
              frameId: cleanElement.frameId || null,
              strokeColor: cleanElement.strokeColor || "#000000",
              backgroundColor: cleanElement.backgroundColor || "transparent",
              isDeleted: Boolean(cleanElement.isDeleted),
              opacity: Number(cleanElement.opacity) || 100,
              roughness: Number(cleanElement.roughness) || 1,
              strokeWidth: Number(cleanElement.strokeWidth) || 1,
              angle: Number(cleanElement.angle) || 0,
              version: Number(cleanElement.version) || 1
            };

            // 为文本元素添加特有属性
            if (cleanElement.type === 'text') {
              baseElement.text = cleanElement.text || '';
              baseElement.fontSize = Number(cleanElement.fontSize) || 20;
              baseElement.fontFamily = Number(cleanElement.fontFamily) || 1;
              baseElement.textAlign = cleanElement.textAlign || 'left';
              baseElement.verticalAlign = cleanElement.verticalAlign || 'top';
              baseElement.containerId = cleanElement.containerId || null;
              baseElement.originalText = cleanElement.originalText || cleanElement.text || '';
              baseElement.lineHeight = Number(cleanElement.lineHeight) || 1.25;
            }

            // 为箭头元素添加特有属性
            if (cleanElement.type === 'arrow' || cleanElement.type === 'line') {
              baseElement.points = Array.isArray(cleanElement.points) ? cleanElement.points : [[0, 0], [100, 100]];
              baseElement.lastCommittedPoint = cleanElement.lastCommittedPoint || null;
              baseElement.startBinding = cleanElement.startBinding || null;
              baseElement.endBinding = cleanElement.endBinding || null;
              baseElement.startArrowhead = cleanElement.startArrowhead || null;
              baseElement.endArrowhead = cleanElement.endArrowhead || 'arrow';
            }

            // 为自由绘制元素添加特有属性
            if (cleanElement.type === 'freedraw') {
              // 确保points数组格式正确，freedraw需要points数组来定义绘制路径
              baseElement.points = Array.isArray(cleanElement.points) ? cleanElement.points : [];
              baseElement.pressures = Array.isArray(cleanElement.pressures) ? cleanElement.pressures : [];
              baseElement.simulatePressure = Boolean(cleanElement.simulatePressure);
              baseElement.lastCommittedPoint = cleanElement.lastCommittedPoint || null;
            }

            // 添加处理后的元素
            processedElements.push(baseElement);
          });

          console.log("🔍 处理后的元素:", processedElements);

          // 直接替换所有元素（移除Scene概念，直接操作元素数组）
          try {
            // 设置标志，防止事件更新触发onChange
            isUpdatingFromRestore.current = true;

            // 确保appState包含必需的collaborators属性
            const safeAppState = ensureCollaboratorsMap(payload.appState);

            apiRef.current.updateScene({
              elements: processedElements,
              appState: safeAppState,
              files: payload.files || {}
            });
            console.log("✅ 画布元素更新成功，元素数量:", processedElements.length);

            // 清除标志
            setTimeout(() => {
              isUpdatingFromRestore.current = false;
            }, 100);

            // 同步后端数据到IndexedDB
            try {
              await indexedDBService.saveCanvasData(processedElements, payload.appState || {});
              console.log("💾 后端数据已同步到IndexedDB");
            } catch (error) {
              console.error("❌ 同步到IndexedDB失败:", error);
            }

            // 注意：绘制操作不需要同步到后端，因为绘制事件本身就是从后端发起的
            console.log("ℹ️ 绘制操作来自后端，无需同步");
          } catch (error) {
            console.error("❌ 画布元素更新失败:", error);
            // 尝试仅更新元素
            try {
              // 设置标志，防止简化版更新触发onChange
              isUpdatingFromRestore.current = true;

              const safeAppState = ensureCollaboratorsMap(payload.appState);
              apiRef.current.updateScene({
                elements: processedElements,
                appState: safeAppState
              });
              console.log("✅ 简化版画布元素更新成功");

              // 清除标志
              setTimeout(() => {
                isUpdatingFromRestore.current = false;
              }, 100);

              // 同步简化版更新到IndexedDB
              try {
                await indexedDBService.saveCanvasData(processedElements, payload.appState || {});
                console.log("💾 简化版数据已同步到IndexedDB");
              } catch (error) {
                console.error("❌ 简化版数据同步到IndexedDB失败:", error);
              }
            } catch (simpleError) {
              console.error("❌ 简化版画布元素更新也失败:", simpleError);
            }
          }
        } else {
          // 清空画布元素
          // 设置标志，防止清空操作触发onChange
          isUpdatingFromRestore.current = true;

          const safeAppState = ensureCollaboratorsMap(payload.appState);
          apiRef.current.updateScene({
            elements: [],
            appState: safeAppState,
            files: payload.files || {}
          });
          console.log("⚠️ 画布已清空");

          // 清除标志
          setTimeout(() => {
            isUpdatingFromRestore.current = false;
          }, 100);

          // 同步清空操作到IndexedDB
          try {
            await indexedDBService.clearCanvasData();
            console.log("💾 IndexedDB数据已清空");
          } catch (error) {
            console.error("❌ 清空IndexedDB失败:", error);
          }
        }
      } catch (error) {
        console.error("❌ 处理画布更新失败:", error);
      }
    } else {
      console.log("❌ apiRef.current 不存在，无法更新画布");
    }
  };

  useEffect(() => {
    let unlisten: UnlistenFn | null = null;

    if (!isTauri) {
      console.log("⚠️ 非Tauri环境，启用轮询机制检测后端数据变化");

      // 在浏览器环境中使用轮询机制检测后端数据变化
      let lastUpdateTime = '';
      const pollInterval = setInterval(async () => {
        try {
          const response = await fetch('http://localhost:31337/canvas');
          if (response.ok) {
            const data = await response.json();
            const canvas = data.canvas;

            // 检查数据是否有更新
            if (canvas && canvas.updated_at && canvas.updated_at !== lastUpdateTime) {
              lastUpdateTime = canvas.updated_at;
              console.log('🔄 检测到后端数据更新，同步到画布');

              // 模拟 Tauri 事件处理逻辑
              const payload = {
                elements: canvas.elements,
                appState: canvas.app_state,
                files: canvas.files
              };

              // 处理画布更新
              await handleCanvasUpdate(payload);
            }
          }
        } catch (error) {
          console.warn('⚠️ 轮询后端数据失败:', error);
        }
      }, 1000); // 每秒检查一次

      return () => {
        clearInterval(pollInterval);
      };
    }

    (async () => {
      console.log("🔧 设置事件监听器: excalidraw_draw");
      console.log("📍 当前时间:", new Date().toISOString());

      unlisten = await listen<DrawPayload>("excalidraw_draw", async (event) => {
        console.log("🎨 收到Tauri绘制事件:", event);
        const payload = event.payload as DrawPayload;

        // 使用统一的画布更新处理逻辑
        await handleCanvasUpdate(payload);
      });
      console.log("✅ 事件监听器设置完成");
    })();
    return () => {
      if (unlisten) {
        console.log("🧹 清理事件监听器");
        unlisten();
      }
    };
  }, []);

  // 获取当前画布数据的函数
  const getCurrentCanvasData = () => {
    if (apiRef.current) {
      const elements = apiRef.current.getSceneElements();
      const appState = apiRef.current.getAppState();
      const files = apiRef.current.getFiles();
      return {
        elements,
        appState,
        files,
        timestamp: new Date().toISOString()
      };
    }
    return null;
  };

  // 打开模态框并获取当前数据
  const openModal = () => {
    const data = getCurrentCanvasData();
    setCanvasData(data);
    setIsModalOpen(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setIsModalOpen(false);
    setCanvasData(null);
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {/* 显示JSON数据的按钮 */}
      <button
        onClick={openModal}
        style={{
          position: "absolute",
          top: "10px",
          right: "10px",
          zIndex: 1000,
          padding: "8px 16px",
          backgroundColor: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
          fontSize: "14px",
          fontWeight: "bold",
          boxShadow: "0 2px 4px rgba(0,0,0,0.2)"
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.backgroundColor = "#45a049";
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.backgroundColor = "#4CAF50";
        }}
      >
        显示JSON数据
      </button>

      {/* Excalidraw画布 */}
      <Excalidraw
        langCode='zh-CN'
        initialData={{
          appState: {
            collaborators: new Map()
          }
        }}
        excalidrawAPI={(api: any) => {
          console.log("🔧 Excalidraw API 已就绪:", !!api);
          console.log("📍 API 设置时间:", new Date().toISOString());
          console.log("🔍 API 对象:", api);
          if (api && api.updateScene) {
            console.log("✅ 画布更新方法可用");
          } else {
            console.log("❌ 画布更新方法不可用");
          }
          apiRef.current = api;
          console.log("✅ apiRef.current 已设置");

          // 添加调试信息
          console.log("🔍 Excalidraw组件初始化完成，onChange事件应该已绑定");

          // 测试onChange事件绑定
          setTimeout(() => {
            console.log("🧪 测试onChange事件绑定状态");
            console.log("🔍 当前画布元素数量:", api.getSceneElements ? api.getSceneElements().length : '无法获取');
          }, 1000);
        }}
        onChange={async (elements, appState, files) => {
          console.log("🎨 画布内容发生变化:", {
            elementsCount: elements ? elements.length : 0,
            appState: appState,
            filesCount: files ? Object.keys(files).length : 0,
            timestamp: new Date().toISOString(),
            isFromRestore: isUpdatingFromRestore.current
          });

          // 如果是数据恢复触发的onChange，跳过保存
          if (isUpdatingFromRestore.current) {
            console.log("ℹ️ 数据恢复触发的onChange，跳过保存");
            return;
          }

          // 确保elements存在且不为空
          if (!elements) {
            console.log("⚠️ elements为空，跳过保存");
            return;
          }

          // 创建数据哈希用于去重
          const mutableElements = [...elements] as any[];
          const safeAppState = ensureCollaboratorsMap(appState);
          const canvasData = {
            elements: mutableElements,
            appState: safeAppState,
            files: files || {}
          };
          const dataHash = JSON.stringify(canvasData);

          // 如果数据没有变化，跳过保存
          if (dataHash === lastSaveDataRef.current) {
            console.log("ℹ️ 数据未变化，跳过保存");
            return;
          }

          // 更新数据哈希
          lastSaveDataRef.current = dataHash;

          // 清除之前的防抖定时器
          if (saveTimeoutRef.current) {
            clearTimeout(saveTimeoutRef.current);
          }

          // 设置防抖定时器，延迟保存到本地
          saveTimeoutRef.current = setTimeout(async () => {
            try {
              // 只保存到IndexedDB，不同步到后端
              console.log("💾 准备保存到本地IndexedDB，元素数量:", mutableElements.length);
              await indexedDBService.saveCanvasData(mutableElements, safeAppState);
              console.log("✅ 画布数据已成功保存到本地IndexedDB");
            } catch (error) {
              console.error("❌ 本地存储保存失败:", error);
              console.error("❌ 错误详情:", {
                elementsType: typeof elements,
                elementsLength: elements ? elements.length : 'N/A',
                appStateType: typeof appState,
                error: error
              });
            }
          }, 300); // 300ms 防抖延迟
        }}
      />

      {/* JSON数据模态框 */}
      {isModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 2000
          }}
          onClick={closeModal}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "20px",
              borderRadius: "8px",
              maxWidth: "80%",
              maxHeight: "80%",
              overflow: "auto",
              boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
              position: "relative"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 模态框标题和关闭按钮 */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
                borderBottom: "1px solid #eee",
                paddingBottom: "10px"
              }}
            >
              <h2 style={{ margin: 0, color: "#333" }}>画布JSON数据</h2>
              <button
                onClick={closeModal}
                style={{
                  background: "none",
                  border: "none",
                  fontSize: "24px",
                  cursor: "pointer",
                  color: "#666",
                  padding: "0",
                  width: "30px",
                  height: "30px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.color = "#333";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.color = "#666";
                }}
              >
                ×
              </button>
            </div>

            {/* JSON数据显示区域 */}
            <div
              style={{
                backgroundColor: "#f5f5f5",
                padding: "15px",
                borderRadius: "4px",
                border: "1px solid #ddd",
                fontFamily: "monospace",
                fontSize: "12px",
                lineHeight: "1.4",
                maxHeight: "500px",
                overflow: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all"
              }}
            >
              {canvasData ? JSON.stringify(canvasData, null, 2) : "暂无数据"}
            </div>

            {/* 复制按钮 */}
            <div style={{ marginTop: "15px", textAlign: "right" }}>
              <button
                onClick={() => {
                  if (canvasData) {
                    navigator.clipboard.writeText(JSON.stringify(canvasData, null, 2))
                      .then(() => alert("JSON数据已复制到剪贴板！"))
                      .catch(() => alert("复制失败，请手动选择文本复制"));
                  }
                }}
                style={{
                  padding: "8px 16px",
                  backgroundColor: "#2196F3",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "14px",
                  marginRight: "10px"
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = "#1976D2";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = "#2196F3";
                }}
              >
                复制JSON
              </button>
              <button
                onClick={closeModal}
                style={{
                  padding: "8px 16px",
                  backgroundColor: "#f44336",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "14px"
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = "#d32f2f";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = "#f44336";
                }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


