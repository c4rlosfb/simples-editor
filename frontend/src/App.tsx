import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import EditorPanel from './components/EditorPanel'
import FileBrowser from './components/FileBrowser'
import OutputPanel from './components/OutputPanel'
import Toolbar from './components/Toolbar'
import './setup-monaco'

export default function App() {
  return (
    <div className="h-screen flex flex-col bg-[#1e1e1e]">
      <Toolbar />
      <div className="flex-1">
        <PanelGroup direction="horizontal">
          <Panel defaultSize={20} minSize={10} maxSize={40}>
            <FileBrowser />
          </Panel>
          <PanelResizeHandle className="w-1 bg-[#333] hover:bg-[#007acc] transition-colors cursor-col-resize" />
          <Panel defaultSize={55} minSize={30}>
            <EditorPanel />
          </Panel>
          <PanelResizeHandle className="w-1 bg-[#333] hover:bg-[#007acc] transition-colors cursor-col-resize" />
          <Panel defaultSize={25} minSize={10} maxSize={40}>
            <OutputPanel />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  )
}
