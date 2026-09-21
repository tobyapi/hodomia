import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { VocalComparison } from './VocalComparison';
import type { VocalComparison as Comparison } from '../types';

const data: Comparison = { schemaVersion: 1, duration: 5, notice: '未校正スコア', variants: [
  { id: 'yamnet-vocals', model: 'yamnet', source: 'vocals', windowSeconds: .975, hopSeconds: .48,
    thresholds: { beatbox: { onset: .15, offset: .1 }, breath: { onset: .15, offset: .1 }, humming: { onset: .15, offset: .1 } },
    frames: [{ start: 1, end: 1.975, scores: { beatbox: .4, breath: 0, humming: 0 }, classScores: { Beatboxing: .4 } }],
    candidates: [{ id: 'y1', start: 1, end: 1.975, label: 'ビートボックス', category: 'beatbox', score: .4, reviewed: false }] },
] };

test('comparison auditions its own source and displays low-scoring classes without inventing candidates', () => {
  const onAudition = vi.fn();
  render(<VocalComparison data={data} duration={5} time={0} zoom={8} ready locked={false} onAnalyze={vi.fn()} onSetup={vi.fn()} onAudition={onAudition} />);
  fireEvent.click(screen.getByRole('button', { name: /YAMNET · ボーカル ビートボックス/ }));
  expect(onAudition).toHaveBeenCalledWith('vocals', 1, 1.975);
  fireEvent.change(screen.getByLabelText('比較する声'), { target: { value: 'breath' } });
  expect(screen.getByText(/この条件で候補はありません/)).toBeVisible();
  expect(screen.getByLabelText('YAMNET · ボーカル ブレス スコア')).toBeVisible();
});

test('setup and comparison controls reflect readiness and the shared job lock', () => {
  const onSetup = vi.fn();
  const props = { duration: 5, time: 0, zoom: 8, onAnalyze: vi.fn(), onSetup, onAudition: vi.fn() };
  const view = render(<VocalComparison {...props} ready={false} locked={false} />);
  fireEvent.click(screen.getByRole('button', { name: 'YAMNetをセットアップ' }));
  expect(onSetup).toHaveBeenCalledOnce();
  view.rerender(<VocalComparison {...props} ready locked />);
  expect(screen.getByRole('button', { name: 'AST / YAMNet を比較' })).toBeDisabled();
});
