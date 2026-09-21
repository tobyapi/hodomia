import { useCallback, useEffect, useRef, useState } from "react";
import * as nativeApi from "./api";
import { beatGrid, effectiveBpm, replaceRow, timeLabel } from "./editing";
import { useCloseSave } from "./useCloseSave";
import { useEdits } from "./useEdits";
import type { AnalysisOptions, Job, Mode, RuntimeStatus, Snapshot, TimelineRow, Track, SavedProject } from "./types";
import { TRACK_NAMES } from "./types";
import { Timeline } from "./components/Timeline";
import { Inspector } from "./components/Inspector";
import { Player } from "./components/Player";
import { ChordControls } from "./components/ChordControls";

const INITIAL_VISIBLE: Record<string, boolean> = { beats: true, sections: true, lyrics: true, words: false, vocalEvents: true, chords: true, key: false, energy: true, pitch: true, stems: false };

export function App({ bridge = nativeApi }: { bridge?: typeof nativeApi } = {}) {
  const api = bridge;
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [beatboxRecall, setBeatboxRecall] = useState(true);
  const [savedProjects, setSavedProjects] = useState<SavedProject[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<SavedProject | null>(null);
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [job, setJob] = useState<Job>({ running: false, kind: null, log: "" });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [mode, setMode] = useState<Mode>("japanese");
  const [eventSensitivity, setEventSensitivity] = useState<"standard" | "sensitive">("standard");
  const [lyrics, setLyrics] = useState("");
  const [track, setTrack] = useState<Track>("sections");
  const [selectedId, setSelectedId] = useState<string>();
  const [visible, setVisible] = useState(INITIAL_VISIBLE);
  const [zoom, setZoom] = useState(8);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [stem, setStem] = useState("original");
  const [loop, setLoop] = useState<{ start: number; end: number } | null>(null);
  const [bpm, setBpm] = useState("120");
  const [anchor, setAnchor] = useState("0");
  const [meter, setMeter] = useState("4");
  const [showLog, setShowLog] = useState(false);
  const [viewAuto, setViewAuto] = useState(false);
  const [draftDirty, setDraftDirty] = useState(false);
  const [externalChange, setExternalChange] = useState(false);
  const editor = useEdits();
  const audio = useRef<HTMLAudioElement>(null);
  const currentTime = useRef(0);
  const switchingAudio = useRef(false);
  const previousRunning = useRef(false);
  const duration = snapshot?.project.duration ?? 1;
  const base = snapshot?.result.tracks ?? {};
  const tracks = viewAuto ? base : { ...base, ...editor.tracks };
  const rows = tracks[track] ?? [];
  const displayedBpm = effectiveBpm(tracks.beats ?? []);
  const selected = rows.find(r => r.id === selectedId);
  const missingVocalCategories = editor.tracks.vocalEvents
    ? (base.vocalEvents ?? []).filter(row => row.method === "vocal-percussion"
      ? !editor.tracks.vocalEvents!.some(saved => saved.category === "beatbox" && saved.start! <= row.start! && saved.end! >= row.end!)
      : (row.category === "rap" || row.category === "spoken") && !editor.tracks.vocalEvents!.some(saved => saved.category === row.category)) : [];
  const locked = busy || job.running;
  const source = snapshot ? (stem === "original" ? snapshot.project.audio : snapshot.result.stems?.[stem]) : null;
  const guarded = useCallback(async (action: () => Promise<void>) => {
    setError(""); setBusy(true);
    try { await action(); } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }, []);

  useEffect(() => {
    if (!api.desktop()) return;
    api.runtimeStatus().then(setRuntime).catch(e => setError(String(e)));
    api.savedProjects().then(setSavedProjects).catch(e => setError("保存した曲を取得できません: " + String(e)));
  }, []);
  useEffect(() => {
    if (!api.desktop()) return;
    let alive = true, polling = false;
    const refresh = async () => {
      if (polling) return;
      polling = true;
      try {
        const next = await api.jobStatus();
        if (!alive) return;
        setJob(next);
        if (!busy) {
          const projects = await api.savedProjects();
          if (!alive) return;
          setSavedProjects(projects);
        }
        if (snapshot && !busy) {
          const value = await api.openProject(snapshot.root);
          if (!alive) return;
          if (value.edits.revision !== snapshot.edits.revision && (editor.dirty || draftDirty)) {
            setExternalChange(true);
          } else if (!draftDirty) {
            if (value.edits.revision !== snapshot.edits.revision) editor.reset(value.edits.tracks);
            setExternalChange(false);
            setSnapshot(value);
          }
        }
        if (previousRunning.current && !next.running) {
          const info = await api.runtimeStatus();
          if (alive) setRuntime(info);
          if (next.success === false && alive) setError("処理が終了しました。ログと解析状態を確認してください。");
        }
        previousRunning.current = next.running;
        if (!busy && !editor.dirty && !draftDirty && !next.running) {
          const request = await api.nextUiRequest();
          if (!alive || !request) return;
          try {
            const value = await api.openProject(request.root);
            if (!alive) return;
            if (request.stem !== "original" && !value.result.stems?.[request.stem]) throw new Error("指定した分離音声がありません。");
            install(value); setTrack(request.track); setStem(request.stem);
            setLoop({ start: request.start, end: request.end });
            currentTime.current = request.start; setTime(request.start);
            if (audio.current && snapshot?.root === request.root && stem === request.stem) audio.current.currentTime = request.start;
            setMessage("AIが指定した区間を開きました。再生ボタンで試聴できます。");
            await api.ackUiRequest(request.requestId, "applied");
          } catch (e) {
            await api.ackUiRequest(request.requestId, "failed", String(e));
            if (alive) setError(String(e));
          }
        }
      } catch (e) { if (alive) setError(String(e)); } finally { polling = false; }
    };
    const timer = window.setInterval(refresh, 1800);
    void refresh();
    return () => { alive = false; window.clearInterval(timer); };
  }, [snapshot?.root, snapshot?.edits.revision, editor.dirty, draftDirty, busy, stem]);
  useEffect(() => {
    if (nativeApi.desktop()) return;
    const handler = (event: BeforeUnloadEvent) => { if (editor.dirty) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [editor.dirty]);
  useEffect(() => {
    if (snapshot?.result.bpm) setBpm(snapshot.result.bpm.toFixed(2));
  }, [snapshot?.result.bpm]);

  function install(value: Snapshot) {
    setExternalChange(false);
    audio.current?.pause(); setSnapshot(value); editor.reset(value.edits.tracks);
    setTime(0); currentTime.current = 0; setPlaying(false); setStem("original"); setLoop(null); setSelectedId(undefined);
    setViewAuto(false); setLyrics(""); setMessage("プロジェクトを開きました。");
    void api.savedProjects().then(setSavedProjects).catch(e => setError("保存した曲の一覧を更新できません: " + String(e)));
  }
  async function save() {
    if (!snapshot) return;
    const edits = await api.saveEdits(snapshot.root, { revision: snapshot.edits.revision, tracks: editor.tracks });
    setSnapshot(s => s ? { ...s, edits } : s); editor.markSaved(); setMessage("修正を保存しました。");
  }
  useCloseSave(editor.dirty, save, setError);
  async function open(create: boolean) {
    if (editor.dirty) await save();
    if (create) {
      const source = await api.choose("source"); if (!source) return;
      setMessage("音源をコピーして読み込んでいます…");
      install(await api.createProject(source));
    } else {
      const root = await api.choose("project"); if (root) install(await api.openProject(root));
    }
  }
  async function start(region?: AnalysisOptions["region"], scope?: "vocal-events" | "harmony") {
    if (!snapshot) return;
    if (editor.dirty) await save();
    setMessage("解析を開始しています…");
    const started = await api.analyze(snapshot.root, { mode, lyrics: region ? (selected?.label ?? "") : lyrics, eventSensitivity, beatboxRecall, ...(region ? { region } : {}), ...(scope ? { scope } : {}) });
    previousRunning.current = true;
    setJob({ running: true, kind: "analysis", log: "", jobId: started.jobId }); setViewAuto(false);
    if (scope) { setTrack(scope === "harmony" ? "chords" : "vocalEvents"); setSelectedId(undefined); }
  }
  function seek(value: number) {
    const next = Math.min(duration, Math.max(0, value));
    if (audio.current) audio.current.currentTime = next;
    setTime(next); currentTime.current = next;
  }
  async function togglePlay() {
    if (!audio.current) return;
    if (audio.current.paused) { try { await audio.current.play(); } catch (e) { setError("再生できません: " + String(e)); } }
    else audio.current.pause();
  }
  function changeRow(row: TimelineRow) {
    editor.change(replaceRow(editor.tracks, base, track, row)); setViewAuto(false); setSelectedId(row.id);
  }
  function addRow() {
    const row: TimelineRow = { id: crypto.randomUUID(), start: time, end: track === "beats" ? time : Math.min(duration, time + 3), label: track === "lyrics" ? "歌詞を入力" : track === "vocalEvents" ? "その他の非言語発声" : "新しい項目", reviewed: false, ...(track === "vocalEvents" ? { category: "other" as const } : {}) };
    changeRow(row);
  }
  const desktop = api.desktop();
  return <div className="app-shell">
    {deleteTarget && <div className="delete-overlay"><section className="delete-dialog" role="dialog" aria-modal="true" aria-label="解析データの削除"><h3>「{deleteTarget.name}」の解析データを削除しますか？</h3><p>解析結果・分離音声・手修正・書き出しデータを削除し、一覧から取り除きます。この操作は元に戻せません。</p><p>元の音源と再生用音声は残します。「プロジェクトを開く」から再登録し、再分析できます。</p><div className="button-row"><button autoFocus disabled={locked} onClick={() => setDeleteTarget(null)}>キャンセル</button><button className="danger" disabled={locked} onClick={() => void guarded(async () => { const root = deleteTarget.root; await api.deleteAnalysis(root); if (snapshot?.root === root) { audio.current?.pause(); setSnapshot(null); editor.reset({}); setPlaying(false); } await api.removeSavedProject(root); setSavedProjects(await api.savedProjects()); setDeleteTarget(null); setMessage("解析データを削除しました。元の音源と再生用音声は残っています。"); })}>解析データを削除</button></div></section></div>}
    <header className="app-header">
      <div className="brand"><span className="brand-mark">M</span><div><strong>Music Sweeper</strong><small>音を読み解き、映像へ。</small></div></div>
      <div className="header-actions"><span className={"runtime-badge " + (runtime?.ready ? "ready" : "")}>{runtime?.ready ? "● ローカル解析 準備完了" : desktop ? "○ 解析環境 未準備" : "ブラウザープレビュー"}</span>
      <button disabled={!desktop || locked} onClick={() => void guarded(() => open(false))}>プロジェクトを開く</button>
      <button className="primary" disabled={!desktop || locked} onClick={() => void guarded(() => open(true))}>＋ 曲を読み込む</button></div>
    </header>
    {(error || message) && <div className={"notice " + (error ? "error-notice" : "")} role={error ? "alert" : "status"}><span>{error || message}</span><button aria-label="通知を閉じる" onClick={() => { setError(""); setMessage(""); }}>×</button></div>}
    <div className="workspace">
      <aside className="sidebar">
        <section className="saved-projects" aria-label="保存した曲"><div className="saved-projects-heading"><strong>保存した曲</strong><button disabled={!desktop || locked} onClick={() => void guarded(async () => setSavedProjects(await api.savedProjects()))}>更新</button></div><p className="muted">解析結果は自動保存されます。曲を選ぶと続きから開けます。</p><div className="saved-project-list">{savedProjects.map(project => <div className="saved-project-item" key={project.root}><button title={project.root} disabled={locked} aria-label={project.name + "を開く"} onClick={() => void guarded(async () => { if (editor.dirty) await save(); install(await api.openProject(project.root)); })}><strong>{project.name}</strong><small>{timeLabel(project.duration)} · {project.hasAnalysis ? "解析履歴あり" : "未解析"}</small><small>{project.createdAt ? new Date(project.createdAt).toLocaleString("ja-JP") : ""}</small></button><button className="remove-saved" disabled={locked} aria-label={project.name + "を削除"} title="解析データを削除" onClick={() => setDeleteTarget(project)}>×</button></div>)}</div>{!savedProjects.length && <p className="muted">保存した曲はまだありません。別の場所のデータは「プロジェクトを開く」で追加できます。</p>}</section>
        <div className="eyebrow">ANALYSIS</div><h2>曲を分析する</h2>
        <label>解析モード<select value={mode} disabled={locked} onChange={e => setMode(e.target.value as Mode)}><option value="japanese">日本語歌唱・精度優先</option><option value="multilingual">多言語の歌もの</option><option value="instrumental">インストゥルメンタル</option></select></label>
        <p className="muted">{mode === "japanese" ? "分離した歌声を日本語に固定して認識し、歌詞の時刻を精密に合わせます。" : mode === "instrumental" ? "歌詞の認識を省き、音楽の構造と主旋律を分析します。" : "言語を自動判別します。歌詞と時刻は推定候補として表示します。"}</p>
        {mode !== "instrumental" && <><label>歌詞（任意）<textarea placeholder={"正しい歌詞があれば貼り付け\n1行＝1フレーズ、繰り返しも曲順に"} rows={6} value={lyrics} disabled={locked} onChange={e => setLyrics(e.target.value)} /></label>
        <button className="text-button" disabled={!desktop || locked} onClick={() => void guarded(async () => { const path = await api.choose("lyrics"); if (path) setLyrics(await api.readLyrics(path)); })}>テキストファイルから読み込む</button></>}
        <button className="primary full" disabled={!snapshot || !runtime?.ready || !runtime?.chordMiniReady || locked} onClick={() => void guarded(() => start())}>{snapshot?.project.currentRun ? "全体を再分析" : "分析を開始"}</button>
        {!runtime?.chordMiniReady && desktop && <div className="event-note"><p className="muted">コード分析にはBTCモデルの準備が必要です。</p><button disabled={!runtime?.ready || locked} onClick={() => void guarded(async () => { await api.setupRuntime(true); setJob({ running: true, kind: "setup", log: "" }); previousRunning.current = true; setShowLog(true); })}>コードモデルをセットアップ</button></div>}
        {snapshot?.project.currentRun && <p className="muted">再分析しても手動修正は保持します。</p>}
        <div className="section-divider"><label>声の表現の検出感度<select value={eventSensitivity} disabled={locked} onChange={e => setEventSensitivity(e.target.value as "standard" | "sensitive")}><option value="standard">標準</option><option value="sensitive">候補を多めに拾う</option></select></label>
          <p className="muted">ラップ・朗読／語り・ビートボックス・ブレス・ハミングの候補を表示。歌詞は削除しません。</p>
          <p className="muted">ラップ・朗読／語りの検出は実験的です。候補が出なくても、その発声がないとは限りません。</p>
          <label className="check-label"><input type="checkbox" checked={beatboxRecall} disabled={locked} onChange={e => setBeatboxRecall(e.target.checked)} />ビートボックスの候補を広く拾う</label><p className="muted">分離ボーカルの打撃音も補助検出します。ラップ・ブレス・楽器漏れを含むため試聴して確認してください。</p>
          <button className="full" disabled={!snapshot || !runtime?.ready || locked} onClick={() => void guarded(() => start(undefined, "vocal-events"))}>声の表現だけ検出</button>
        </div>
        {job.running && <button className="full danger" disabled={job.cancelRequested} onClick={() => void guarded(async () => { await api.cancelJob(job.jobId); setMessage("中止を要求しました。現在の処理の区切りまで待っています。"); })}>{job.cancelRequested ? "中止待ち…" : "処理を中止"}</button>}
        <div className="section-divider"><div className="eyebrow">TRACKS</div>
          {Object.entries({ ...TRACK_NAMES, energy: "盛り上がり", pitch: "主旋律", stems: "楽器の出入り" }).map(([id, name]) => <label className="track-toggle" key={id}><input type="checkbox" checked={visible[id]} onChange={e => setVisible({ ...visible, [id]: e.target.checked })} />{name}</label>)}
        </div>
        <div className="runtime-box"><span>ローカル環境</span><small>{runtime?.details?.cudaAvailable ? "GPU / CUDA" : runtime?.ready ? "CPU" : "初回のみダウンロードが必要です"}</small>
          <button disabled={!desktop || locked} onClick={() => void guarded(async () => { await api.setupRuntime(); setJob({ running: true, kind: "setup", log: "" }); previousRunning.current = true; setShowLog(true); })}>{runtime?.ready ? "環境を再確認・修復" : "初回セットアップ"}</button>
          <button className="text-button" onClick={() => setShowLog(!showLog)}>処理ログ {showLog ? "を閉じる" : "を表示"}</button>
        </div>
      </aside>
      <main className="main-panel">
      {snapshot ? <>
        {externalChange && <div role="alert" className="error">AIまたは別の画面で保存内容が更新されました。手元の変更は保持しています。
          <button onClick={() => { if (window.confirm("手元の未保存の変更を破棄し、最新の保存内容を読み込みますか？")) void guarded(async () => install(await api.openProject(snapshot.root))); }}>最新の保存内容を読み込む</button>
        </div>}
        <div className="project-heading"><div><div className="eyebrow">SONG WORKSPACE</div><h1>{snapshot.project.name}</h1><p className="muted">{timeLabel(duration)} · {displayedBpm ? displayedBpm.toFixed(1) + (editor.tracks.beats && !viewAuto ? " BPM（修正）" : " BPM（推定）") : "BPM 未解析"} · {(tracks.key ?? [])[0]?.label ?? "キー 未解析"}</p></div>
          <div className="button-row"><button disabled={!editor.canUndo || busy} onClick={editor.undo}>元に戻す</button><button disabled={!editor.canRedo || busy} onClick={editor.redo}>やり直す</button><button disabled={!editor.dirty || busy} onClick={() => void guarded(save)}>{editor.dirty ? "● 修正を保存" : "保存済み"}</button>
          <button disabled={busy || job.running} onClick={() => void guarded(async () => { if (editor.dirty) await save(); const result = await api.exportProject(snapshot.root); setMessage("書き出しました: " + result.path + (result.untimedLyrics ? "（時刻未確定の歌詞は字幕から除外）" : "")); })}>書き出し ↗</button></div>
        </div>
        <Player playing={playing} time={time} duration={duration} stem={stem}
          stems={Object.keys(snapshot.result.stems ?? {})} looping={!!loop} zoom={zoom} audio={audio} sourceKey={snapshot.root + "/" + source}
          onPlay={() => void togglePlay()} onSeek={seek} onStem={value => { switchingAudio.current = true; audio.current?.pause(); setStem(value); }}
          onLoop={() => setLoop(loop ? null : { start: 0, end: duration })} onZoom={setZoom} />
        <audio ref={audio} src={source ? api.asset(snapshot.root, source) : undefined} onLoadedMetadata={() => { if (audio.current) audio.current.currentTime = currentTime.current; switchingAudio.current = false; }} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} onTimeUpdate={() => {
          if (!audio.current || switchingAudio.current) return; const t = audio.current.currentTime;
          if (loop && (t >= loop.end || t < loop.start)) { audio.current.currentTime = loop.start; return; }
          currentTime.current = t; setTime(t);
        }} onError={() => setError("音声を再生できません。プロジェクト内の音声ファイルを確認してください。")} />
        <div className="analysis-progress"><span>{job.running && job.kind === "analysis" ? snapshot.status.stage : snapshot.status.state === "running" ? "前回の解析は中断されています。再分析できます。" : snapshot.status.stage}</span>
          <span>{snapshot.status.elapsed ? Math.round(snapshot.status.elapsed) + " 秒" : ""}</span><progress max={1} value={snapshot.status.progress ?? 0} /></div>
        <Timeline duration={duration} time={time} zoom={zoom} tracks={tracks} analysis={snapshot.result} visible={visible} selected={selectedId} onSeek={seek} onSelect={(t, row) => { setTrack(t); setSelectedId(row.id); }} />
        {track === "vocalEvents" && <p className="muted event-note">{snapshot.result.engines?.vocalEvents ? "検出結果は候補です。通常の歌唱や楽器との取り違え、短い息の見逃しがあります。" : "声の表現はまだ検出していません。「声の表現だけ検出」で追加できます。"} 歌詞と重なる候補も表示します。「あー」「うー」やスキャットは必要に応じて手動で分類してください。</p>}
        <div className="editor-toolbar"><select aria-label="編集トラック" value={track} onChange={e => { setTrack(e.target.value as Track); setSelectedId(undefined); }}>{Object.entries(TRACK_NAMES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select>
        <button disabled={viewAuto || busy} onClick={addRow}>＋ 再生位置に追加</button><label className="check-label"><input type="checkbox" checked={viewAuto} onChange={e => setViewAuto(e.target.checked)} />自動結果を比較</label>
        {editor.tracks[track] && <button disabled={busy} onClick={() => { const next = { ...editor.tracks }; delete next[track]; editor.change(next); setViewAuto(false); }}>このトラックを自動結果へ戻す</button>}<span className="muted">{rows.length} 項目</span></div>
        {track === "vocalEvents" && !viewAuto && missingVocalCategories.length > 0 && <div className="event-note"><p className="muted">手修正に含まれない分類の自動候補が{missingVocalCategories.length}件あります。現在の修正を保持して追加できます。</p><button disabled={locked} onClick={() => editor.change({ ...editor.tracks, vocalEvents: [...editor.tracks.vocalEvents!, ...missingVocalCategories.map(row => ({ ...row, id: crypto.randomUUID() }))].sort((a, b) => (a.start ?? 0) - (b.start ?? 0)) })}>未追加の声の分類を取り込む</button></div>}
        {track === "chords" && <ChordControls analysis={snapshot.result}
          ready={!!runtime?.chordMiniReady} locked={!runtime?.ready || locked} onAnalyze={() => void guarded(() => start(undefined, "harmony"))} />}
        {track === "beats" && <div className="beat-editor"><label>BPM<input aria-label="BPM" type="number" value={bpm} onChange={e => setBpm(e.target.value)} /></label><label>開始秒<input type="number" value={anchor} onChange={e => setAnchor(e.target.value)} /></label><label>小節の拍数<input type="number" value={meter} onChange={e => setMeter(e.target.value)} /></label><button onClick={() => { try { editor.change({ ...editor.tracks, beats: beatGrid(Number(bpm), Number(anchor), duration, Number(meter)) }); setViewAuto(false); } catch (e) { setError(String(e)); } }}>開始位置から拍を再配置</button></div>}
        <div className="rows-table"><table><thead><tr><th>開始</th><th>終了</th><th>内容</th><th>確認</th></tr></thead><tbody>{rows.map(row => <tr key={row.id} className={selectedId === row.id ? "selected-row" : ""} onClick={() => { setSelectedId(row.id); if (row.start !== null) seek(row.start); }}><td>{row.start === null ? "未確定" : timeLabel(row.start)}</td><td>{row.end === null ? "—" : timeLabel(row.end)}</td><td><button className="row-select" onClick={() => setSelectedId(row.id)}>{row.label}{row.uncertain ? "（候補）" : ""}</button></td><td>{row.reviewed ? "確認済み" : "要確認"}</td></tr>)}</tbody></table>{!rows.length && <p className="empty-rows">このトラックにはまだ項目がありません。分析するか、手動で追加できます。</p>}</div>
        {!!snapshot.status.errors.length && <section className="analysis-errors"><h3>確認が必要な解析</h3>{snapshot.status.errors.map((e, i) => <p key={i}><strong>{e.stage}</strong> — {e.message}</p>)}</section>}
      </> : <div className="empty-state"><div className="empty-wave">▂ ▄ ▆ ▃ █ ▅ ▂ ▇ ▄ ▆ ▂</div><div className="eyebrow">LISTEN DEEPER. CREATE BETTER.</div><h1>曲の展開を、ひとつの時間軸に。</h1><p>拍、歌詞、コード、楽器の出入り。<br />MVのアイデアにつながる音の変化を見つけましょう。</p><button className="primary" disabled={!desktop || locked} onClick={() => void guarded(() => open(true))}>最初の曲を読み込む</button><small>MP3 · MP4 · M4A · WAV · FLAC / 15分まで</small>{!desktop && <p className="muted">ファイルの分析はデスクトップアプリで利用できます。</p>}</div>}
      {showLog && <section className="log-panel"><h3>処理ログ</h3><p className="muted">{runtime?.path}</p><pre>{job.log || "まだログはありません。"}</pre></section>}
      </main>
      <aside className="inspector"><div className="eyebrow">DETAILS</div>
        {selected && !viewAuto ? <Inspector key={selected.id + JSON.stringify(selected)} track={track} row={selected} duration={duration} onDirtyChange={setDraftDirty} onSave={changeRow} onDelete={() => { editor.change({ ...editor.tracks, [track]: rows.filter(r => r.id !== selected.id) }); setSelectedId(undefined); }} onLoop={() => { if (selected.start !== null && selected.end !== null) { setLoop({ start: selected.start, end: selected.end }); seek(selected.start); } }} onRegion={language => { if (selected.start !== null && selected.end !== null) void guarded(() => start({ start: selected.start!, end: selected.end!, language })); }} /> :
        <div className="inspector-empty"><span>⌁</span><h3>{viewAuto ? "自動結果を比較中" : "気になる区間を選択"}</h3><p>タイムラインや一覧から項目を選ぶと、内容と時刻を修正できます。</p><p>未確認の推定は、試聴して確かめてください。</p></div>}
      </aside>
    </div>
    <footer><span>LOCAL FIRST · 音源は外部へ送信しません</span><span>{snapshot ? snapshot.root : "Music Sweeper"}{editor.dirty ? " · 未保存の変更あり" : ""}</span></footer>
  </div>;
}
