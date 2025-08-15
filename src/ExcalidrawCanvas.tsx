import { Excalidraw } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import { listen, UnlistenFn } from "@tauri-apps/api/event";
import { useEffect, useRef } from "react";

type DrawPayload = {
  elements?: any;
  appState?: any;
  files?: any;
};

export function ExcalidrawCanvas() {
  const apiRef = useRef<any | null>(null);

  useEffect(() => {
    let unlisten: UnlistenFn | null = null;
    (async () => {
      console.log("🔧 设置事件监听器: excalidraw_draw");
      console.log("📍 当前时间:", new Date().toISOString());

      unlisten = await listen<DrawPayload>("excalidraw_draw", async (event) => {
        console.log("🎨 收到绘制事件:", event);
        console.log("📦 事件payload:", JSON.stringify(event.payload, null, 2));
        const payload = event.payload as DrawPayload;

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

                // 添加处理后的元素
                processedElements.push(baseElement);
              });

              console.log("🔍 处理后的元素:", processedElements);

              // 直接替换所有元素（移除Scene概念，直接操作元素数组）
              try {
                apiRef.current.updateScene({
                  elements: processedElements,
                  appState: payload.appState || {},
                  files: payload.files || {}
                });
                console.log("✅ 画布元素更新成功，元素数量:", processedElements.length);

                // 注意：绘制操作不需要同步到后端，因为绘制事件本身就是从后端发起的
                console.log("ℹ️ 绘制操作来自后端，无需同步");
              } catch (error) {
                console.error("❌ 画布元素更新失败:", error);
                // 尝试仅更新元素
                try {
                  apiRef.current.updateScene({
                    elements: processedElements
                  });
                  console.log("✅ 简化版画布元素更新成功");
                } catch (simpleError) {
                  console.error("❌ 简化版画布元素更新也失败:", simpleError);
                }
              }
            } else {
              // 清空画布元素
              apiRef.current.updateScene({
                elements: [],
                appState: payload.appState || {},
                files: payload.files || {}
              });
              console.log("⚠️ 画布已清空");

              // 注意：清空操作不需要同步到后端，因为清空事件本身就是从后端发起的
              console.log("ℹ️ 清空操作来自后端，无需同步");
            }
          } catch (error) {
            console.error("❌ 画布元素操作失败:", error);
          }
        } else {
          console.log("❌ apiRef.current 为空，无法更新画布");
          console.log("🔍 apiRef 状态:", apiRef);
        }
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

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <Excalidraw
        langCode='zh-CN'
        isCollaborating
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
        }}
      />
    </div>
  );
}


