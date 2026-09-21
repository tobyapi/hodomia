import type { WorkspaceModel } from "../workspace/useWorkspace";
import { AnalysisErrors } from "./AnalysisErrors";
import { AnalysisProgress } from "./AnalysisProgress";
import { BeatEditor } from "./BeatEditor";
import { ChordAnalysis } from "./ChordAnalysis";
import { DeleteDialog } from "./DeleteDialog";
import { DetailsPanel } from "./DetailsPanel";
import { EditorToolbar } from "./EditorToolbar";
import { EmptyState } from "./EmptyState";
import { ExternalChanges } from "./ExternalChanges";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { Notice } from "./Notice";
import { PlaybackPanel } from "./PlaybackPanel";
import { ProcessingLog } from "./ProcessingLog";
import { ProjectHeading } from "./ProjectHeading";
import { ProjectTimeline } from "./ProjectTimeline";
import { RowsTable } from "./RowsTable";
import { Sidebar } from "./Sidebar";
import { VocalCandidateMerge } from "./VocalCandidateMerge";
import { VocalNotice } from "./VocalNotice";
export function AppView({ model }: { model: WorkspaceModel }) {
  const { snapshot } = model;
  return <div className="app-shell">
    <DeleteDialog model={model} />
    <Header model={model} />
    <Notice model={model} />
    <div className="workspace">
      <Sidebar model={model} />
      <main className="main-panel">
        {snapshot ? <>
          <ExternalChanges model={model} />
          <ProjectHeading model={model} />
          <PlaybackPanel model={model} />
          <AnalysisProgress model={model} />
          <ProjectTimeline model={model} />
          <VocalNotice model={model} />
          <EditorToolbar model={model} />
          <VocalCandidateMerge model={model} />
          <ChordAnalysis model={model} />
          <BeatEditor model={model} />
          <RowsTable model={model} />
          <AnalysisErrors model={model} />
        </> : <EmptyState model={model} />}
        <ProcessingLog model={model} />
      </main>
      <DetailsPanel model={model} />

    </div>
    <Footer model={model} />

  </div>;
}
