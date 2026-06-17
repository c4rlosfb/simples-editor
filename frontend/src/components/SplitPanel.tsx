import { useCallback, useEffect, useRef, useState } from "react";

interface SplitPanelProps {
  left: React.ReactNode;
  right: React.ReactNode;
  /** Initial left panel ratio (0–1). Default: 0.6 */
  defaultRatio?: number;
  /** Minimum left panel ratio. Default: 0.2 */
  minRatio?: number;
  /** Maximum left panel ratio. Default: 0.9 */
  maxRatio?: number;
  /** Width of the right panel when collapsed in px. Default: 0 */
  collapsedRightWidth?: number;
}

function SplitPanel({
  left,
  right,
  defaultRatio = 0.6,
  minRatio = 0.2,
  maxRatio = 0.9,
  collapsedRightWidth = 0,
}: SplitPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ratio, setRatio] = useState(defaultRatio);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const prevRatioRef = useRef(defaultRatio);
  const draggingRef = useRef(false);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const handleDoubleClick = useCallback(() => {
    if (isCollapsed) {
      setIsCollapsed(false);
      setRatio(prevRatioRef.current);
    } else {
      prevRatioRef.current = ratio;
      setIsCollapsed(true);
    }
  }, [isCollapsed, ratio]);

  // Track mouse move/up at the document level during drag
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onMouseMove = (e: MouseEvent) => {
      if (!draggingRef.current) return;

      const rect = container.getBoundingClientRect();
      let newRatio = (e.clientX - rect.left) / rect.width;
      newRatio = Math.max(minRatio, Math.min(maxRatio, newRatio));
      setRatio(newRatio);
      setIsCollapsed(false);
    };

    const onMouseUp = () => {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [minRatio, maxRatio]);

  const leftStyle: React.CSSProperties = isCollapsed
    ? { flex: "1", width: "100%" }
    : { flex: `${ratio}` };

  const rightStyle: React.CSSProperties = isCollapsed
    ? { flex: "none", width: collapsedRightWidth, overflow: "hidden" }
    : { flex: "1" };

  return (
    <div ref={containerRef} className="split-panel">
      <div className="split-panel__left" style={leftStyle}>
        {left}
      </div>

      <div
        className="split-panel__divider"
        onMouseDown={handleMouseDown}
        onDoubleClick={handleDoubleClick}
      />

      <div className="split-panel__right" style={rightStyle}>
        {right}
      </div>
    </div>
  );
}

export default SplitPanel;
